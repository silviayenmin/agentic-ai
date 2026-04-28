import os
import re
import datetime
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage, SystemMessage
from logger import log


class ChatAgent(BaseAgent):
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)
        # Create a "clean" LLM without tools for pure conversational responses
        self.clean_llm = self._init_llm(with_tools=False)

    def _init_llm(self, with_tools=True):
        provider_name = self.agent_config.get("provider_override") or self.global_config.get("active_provider")
        providers = self.global_config.get("providers", {})
        config = providers[provider_name]
        p_type = config.get("provider_type")

        from langchain_ollama import ChatOllama
        from langchain_openai import ChatOpenAI
        from langchain_anthropic import ChatAnthropic

        if p_type == "ollama":
            llm = ChatOllama(model=config["model"], base_url=config["base_url"], temperature=config.get("temperature", 0))
        elif p_type == "openai":
            llm = ChatOpenAI(model=config["model"], temperature=config.get("temperature", 0))
        elif p_type == "anthropic":
            llm = ChatAnthropic(model=config["model"], temperature=config.get("temperature", 0))
        
        if with_tools:
            tools = self._load_tools(self.agent_config.get("tools", []))
            if tools:
                return llm.bind_tools(tools)
        return llm

    def _clean_reply(self, text: str) -> str:
        """Strip raw JSON / code-block artifacts and leaked internal phrases."""
        # 1. Remove blocks
        text = re.sub(r"```[a-z]*\n.*?```", "", text, flags=re.DOTALL)
        # 2. Remove tool call patterns
        text = re.sub(r'\{[^{}]*"name"\s*:\s*"[^"]+?"[^{}]*\}', "", text, flags=re.DOTALL)
        
        # 3. Strip robotic/filler patterns
        leaked_patterns = [
            r"I'?m not able to provide a tool call response[^.]*\.",
            r"I don'?t have any tool calls or function responses[^.]*\.",
            r"My previous response was an error on my part[^.]*\.",
            r"[Tt]his question doesn'?t require (a tool|one)[^.]*\.",
            r"I must point out that the functions provided[^.]*\.",
            r"To answer the question \"[^\"]*\", I will use the [^ ]* function[^.]*\.",
            r"I will use the `[^`]*` function to[^.]*\.",
            r"I'm happy to help you with [^.]*! However,[^.]*\.",
            r"Here's an example JSON object that calls this function[^.]*\.",
            r"I can'?t provide a JSON response[^.]*\.",
            r"the prompt doesn'?t require any function calls[^.]*\.",
            r"I'm not a tool, but I can provide some general information[^.]*\.",
            r"since you asked for a JSON response in the format[^.]*\.",
            r"I'll provide a placeholder response[^.]*\.",
        ]
        for pattern in leaked_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
            
        # 4. Generic cleanup for any remaining "tool" talk
        text = re.sub(r"I will use the [a-z0-9_]+ function[^.]*\.", "", text, flags=re.IGNORECASE)
        
        # 5. Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    async def chat(self, user_input: str) -> str:
        # Detect if user is asking for code
        coding_keywords = ["write a program", "write code", "provide a script", "generate code", "python program", "javascript code", "example for if else", "c language"]
        is_coding_request = any(kw in user_input.lower() for kw in coding_keywords)

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_msg = SystemMessage(content=f"The current system time is {now}.")

        history = self.memory.load_memory_variables({})["chat_history"]
        messages = [self.system_prompt, time_msg] + history + [HumanMessage(content=user_input)]

        # --- System Task Gate ---
        # We only run the Action Detection pass if the query contains keywords related to system tasks.
        # This prevents 'trigger-happy' tool calls for simple chat instructions.
        system_keywords = [
            "disk", "space", "usage", "file", "folder", "directory", "path", 
            "process", "stop", "kill", "permission", "time", "memory", "stats",
            "shutdown", "restart", "hack", "wifi", "delete", "remove", "ls", "cd"
        ]
        needs_system_task = any(kw in user_input.lower() for kw in system_keywords) and not is_coding_request

        if needs_system_task:
            # --- Round 1: Action Detection (Conservative) ---
            action_system_prompt = SystemMessage(content="""You are a system assistant. 
RULES:
1. ONLY use tools if the user EXPLICITLY asks to check, list, or manage something on the system.
2. If the user is just chatting or giving formatting instructions, DO NOT use tools.
3. If the user asks for something vague like 'files', use 'list_directory'.
4. NEVER use tools for '/path/to/file.txt' - that is a placeholder.""")
            
            action_messages = [action_system_prompt] + history + [HumanMessage(content=user_input)]
            response = await self.llm.ainvoke(action_messages)
        else:
            # Skip tool detection for pure chat
            response = AIMessage(content="")

        # Execute tools ONLY if a tool was actually requested and it's not a hallucination
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_messages = []
            for tc in response.tool_calls:
                tc = tc if isinstance(tc, dict) else tc.dict()
                tool_name = tc.get("name", "")
                tool_args = tc.get("args", {})
                tool_id   = tc.get("id", tool_name)
                
                # Filter out placeholder hallucinations
                target_path = str(tool_args.get("file_path", "") or tool_args.get("path", ""))
                if "/path/to/" in target_path or "file.txt" in target_path:
                    continue

                # Safety check for destructive commands
                if tool_name == "execute_command":
                    cmd = tool_args.get("command", "").lower()
                    if any(bad in cmd for bad in ["rm ", "del ", "format ", "rf "]):
                        log.warn("ChatAgent", f"Blocked potentially destructive command: {cmd}")
                        tool_messages.append(ToolMessage(content="Error: Destructive commands are blocked for safety.", tool_call_id=tool_id))
                        continue

                log.info("ChatAgent", f"Executing tool: {tool_name}")
                tool_result = await self.run_tool(tool_name, tool_args)
                tool_messages.append(ToolMessage(content=tool_result, tool_call_id=tool_id))

            if tool_messages:
                # Summary phase using the CLEAN LLM
                summary_messages = messages + [response] + tool_messages
                summary_messages.insert(0, SystemMessage(content="Summarize the results naturally. DO NOT mention tool names."))
                summary_response = await self.clean_llm.ainvoke(summary_messages)
                final_output = self._clean_reply(summary_response.content)
            else:
                # If all tool calls were filtered out, just chat
                clean_response = await self.clean_llm.ainvoke(messages)
                final_output = self._clean_reply(clean_response.content)
        else:
            # General chat — use the CLEAN LLM directly to avoid any tool-calling bias
            clean_response = await self.clean_llm.ainvoke(messages)
            final_output = self._clean_reply(clean_response.content)

        self.memory.save_context({"input": user_input}, {"output": final_output})
        return final_output
