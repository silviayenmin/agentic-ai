import os
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


class DependencyCheckerAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)
        
        # Correctly map tool names from config to tool functions
        tool_names = self.agent_config.get("tools", [])
        loaded_tools = self._load_tools(tool_names)
        self.tools = {name: tool for name, tool in zip(tool_names, loaded_tools)}
        print(f"[DependencyChecker] Tools Loaded: {list(self.tools.keys())}", flush=True)

    async def check_dependencies(self, query: str) -> str:
        """
        Analyzes dependencies using tools and saves the report to .agent_context/dependencies.md.
        """
        import sys
        import re
        import json
        
        history = self.memory.load_memory_variables({})["chat_history"]
        
        # Add a strict instruction to use tools first
        strict_query = (
            f"QUERY: {query}\n\n"
            "INSTRUCTION: Search the codebase FIRST. If you need to search, use: Action: tool_name({\"arg\": \"val\"})"
        )
        
        messages = [self.system_prompt] + history + [HumanMessage(content=strict_query)]

        final_response = ""
        # Tool calling loop (ReAct pattern)
        for i in range(30):  # Increased limit for deep analysis
            print(f"\n[DependencyChecker] Iteration {i+1}...", flush=True)
            response = await self.llm.ainvoke(messages)
            content = response.content
            final_response = content
            messages.append(response)

            # 1. Check for API-style tool calls
            tool_calls = getattr(response, "tool_calls", [])
            
            # 2. Check for Text-style tool calls (Action: tool_name({...}))
            action_match = re.search(r"Action:\s*(\w+)\s*\((.*)\)", content, re.DOTALL)
            
            if not tool_calls and not action_match:
                # If the last response was too short or looks like a polite brush-off,
                # force one more call to get a real report.
                is_polite_brush_off = any(phrase in content.lower() for phrase in ["thank you", "feel free to ask", "assistance with this project"])
                if len(content) < 250 or is_polite_brush_off:
                    print("[DependencyChecker] Response looks like a brush-off, forcing a summary...", flush=True)
                    messages.append(HumanMessage(content="You have not provided the actual details I asked for. Based on the tool results above, provide the final detailed report now. DO NOT say 'thank you' or 'feel free to ask', just give the report."))
                    response = await self.llm.ainvoke(messages)
                    final_response = response.content
                else:
                    final_response = content
                print("[DependencyChecker] Finishing.", flush=True)
                break

            # Process API Tool Calls
            for tool_call in tool_calls:
                tool_name = tool_call["name"].split(".")[-1]
                print(f"[DependencyChecker] API Tool Call: {tool_name}", flush=True)
                await self._run_tool(tool_name, tool_call["args"], tool_call["id"], messages)

            # Process Text Tool Calls
            if action_match:
                tool_name = action_match.group(1)
                tool_args_str = action_match.group(2).strip()
                print(f"[DependencyChecker] Text Tool Call: {tool_name}", flush=True)
                try:
                    # Clean up JSON if LLM added single quotes or other mess
                    tool_args_str = tool_args_str.replace("'", "\"")
                    tool_args = json.loads(tool_args_str)
                    await self._run_tool(tool_name, tool_args, f"text_{i}", messages)
                except Exception as e:
                    messages.append(HumanMessage(content=f"Error parsing tool arguments: {e}"))

        self.memory.save_context({"input": query}, {"output": final_response})
        
        # Save dependency report
        dep_path = ".agent_context/dependencies.md"
        os.makedirs(os.path.dirname(dep_path), exist_ok=True)
        with open(dep_path, "w", encoding="utf-8") as f:
            f.write(final_response)
            
        return final_response

    async def _run_tool(self, name, args, call_id, messages):
        if name in self.tools:
            try:
                # Use ainvoke to handle both sync and async tools correctly
                result = await self.tools[name].ainvoke(args)
                messages.append(ToolMessage(tool_call_id=call_id, content=str(result)))
                print(f"[DependencyChecker] Tool Result: Success", flush=True)
            except Exception as e:
                messages.append(ToolMessage(tool_call_id=call_id, content=f"Error: {e}"))
                print(f"[DependencyChecker] Tool Result: Error: {e}", flush=True)
        else:
            messages.append(ToolMessage(tool_call_id=call_id, content=f"Tool {name} not found."))
            print(f"[DependencyChecker] Tool Result: Not Found", flush=True)
