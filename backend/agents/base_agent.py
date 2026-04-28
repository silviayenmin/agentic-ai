import os
import json
import sys
import re
import uuid
import asyncio
from typing import Dict, Any, List
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_classic.memory import ConversationBufferMemory
from dotenv import load_dotenv
from logger import log
from config_loader import get_workspace_dir

load_dotenv()

class BaseAgent:
    def __init__(self, agent_dir: str, global_config_path: str = "config.json"):
        self.agent_dir = agent_dir
        self.global_config = self._load_json(global_config_path)
        # Load system prompt
        with open(os.path.join(agent_dir, "config.json"), "r") as f:
            config = json.load(f)
            
        base_prompt = config["system_prompt"]
        
        self.agent_config = config
        self.name = self.agent_config.get("name", "Unknown Agent")
        self.description = self.agent_config.get("description", "")
        
        # DYNAMIC CONTEXT INJECTION
        env_context = f"\n\n[ENVIRONMENT CONTEXT]\n- Operating System: {sys.platform}\n- Workspace Root: {get_workspace_dir()}\n- All tools operate relative to this root. Do NOT use absolute paths."
        
        # Tool Documentation Injection
        tool_names = self.agent_config.get("tools", [])
        tool_docs = self._generate_tool_docs(tool_names)
        
        full_prompt = base_prompt + env_context + tool_docs
        self.system_prompt = SystemMessage(content=full_prompt)
        
        self.llm = self._init_llm()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True
        )

    def set_chat_history(self, history: List[str]):
        """Injects external history strings into the agent's memory."""
        self.memory.clear()
        for msg in history:
            # We treat previous agent outputs as AI messages to provide context
            self.memory.chat_memory.add_ai_message(msg)

    def _load_json(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            return json.load(f)

    def _init_llm(self):
        # ... (unchanged)
        provider_name = self.agent_config.get("provider_override") or self.global_config.get("active_provider")
        providers = self.global_config.get("providers", {})
        
        if provider_name not in providers:
            raise ValueError(f"Provider '{provider_name}' not found in config.json")
            
        config = providers[provider_name]
        p_type = config.get("provider_type")
        
        # 2. Instantiate the correct LangChain class
        if p_type == "ollama":
            llm = ChatOllama(
                model=config["model"],
                base_url=config["base_url"],
                temperature=config.get("temperature", 0)
            )
        elif p_type == "openai":
            llm = ChatOpenAI(
                model=config["model"],
                temperature=config.get("temperature", 0),
                api_key=os.getenv("OPENAI_API_KEY")
            )
        elif p_type == "anthropic":
            llm = ChatAnthropic(
                model=config["model"],
                temperature=config.get("temperature", 0),
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        else:
            raise ValueError(f"Unsupported provider type: {p_type}")
        
        # 3. Bind tools if any
        tools = self._load_tools(self.agent_config.get("tools", []))
        if tools:
            # Note: ChatOllama and other Chat models support bind_tools
            return llm.bind_tools(tools)
        return llm

    async def invoke_llm(self, messages: List[Any], max_retries: int = 10, retry_count: int = 0) -> Any:
        last_error = None
        workflow_attempt = retry_count + 1

        for attempt in range(1, max_retries + 1):
            try:
                log.llm_call(self.name, attempt, workflow_attempt)

                # DYNAMIC STATE INJECTION
                # We inject the current global state (tasks) into the system prompt message dynamically
                if messages and isinstance(messages[0], SystemMessage):
                    current_state = self.get_current_state()
                    # IMPORTANT: Create a NEW SystemMessage to avoid modifying self.system_prompt permanently
                    original_content = self.system_prompt.content
                    messages[0] = SystemMessage(content=original_content + current_state)

                response = await self.llm.ainvoke(messages)
                log.llm_ok(self.name, workflow_attempt)

                content = getattr(response, 'content', str(response))
                tool_calls = getattr(response, 'tool_calls', [])
                if tool_calls:
                    log.step(self.name, f"LLM returned {len(tool_calls)} tool call(s): {[tc.get('name') for tc in tool_calls]}")
                elif content:
                    preview = content[:200].replace('\n', ' ')
                    log.step(self.name, f"LLM text response: {preview}{'...' if len(content) > 200 else ''}")
                else:
                    log.warn(self.name, "LLM returned empty content and no tool calls")

                return response
            except Exception as e:
                last_error = e
                log.llm_fail(self.name, attempt, max_retries, e)
                if attempt < max_retries:
                    wait_time = attempt * 2
                    log.llm_retry(self.name, wait_time)
                    await asyncio.sleep(wait_time)

        log.llm_exhausted(self.name, max_retries)
        raise last_error

    def _get_available_tools(self) -> Dict[str, Any]:
        """Returns the registry of available tools."""
        import Tools
        return {
            "check_file_permissions": Tools.check_file_permissions,
            "request_os_permission":  Tools.request_os_permission,
            "execute_command":        Tools.execute_command,
            "stop_process":           Tools.stop_process,
            "read_file":              Tools.read_file_tool,
            "write_file":             Tools.write_to_file,
            "find_file":              Tools.find_file,
            "search_code":            Tools.search_code,
            "check_file_exists":      Tools.check_file_exists,
            "web_search":             Tools.web_search_tool,
            "create_file":            Tools.create_file_tool,
            "list_directory":         Tools.list_directory_tool,
            "delete_file":            Tools.delete_file_tool,
            "delete_directory":       Tools.delete_directory_tool,
            "update_task_status":     Tools.update_task_status,
            "get_task_list":          Tools.get_task_list,
        }

    def _load_tools(self, tool_names: List[str]):
        try:
            available_tools = self._get_available_tools()
            bound, skipped = [], []
            for name in tool_names:
                if name in available_tools:
                    bound.append(available_tools[name])
                else:
                    skipped.append(name)

            if bound:
                log.step(self.name, f"Tools bound: {[t for t in tool_names if t in available_tools]}")
            if skipped:
                log.warn(self.name, f"Unknown tools skipped (not in registry): {skipped}")
            return bound
        except ImportError as e:
            log.warn(self.name, f"Could not import Tools module: {e}")
            return []

    # Normalize tool names that LLMs commonly get wrong.
    _TOOL_ALIASES: Dict[str, str] = {
        "list_directory": "list_directory_tool",
        "read_file": "read_file_tool",
        "create_file": "create_file_tool",
        "web_search": "web_search_tool",
        "delete_file": "delete_file_tool",
    }

    # Normalize argument keys that LLMs commonly get wrong.
    _ARG_ALIASES: Dict[str, Dict[str, str]] = {
        "write_to_file":    {"file_path": "file_name", "filename": "file_name", "path": "file_name"},
        "create_file_tool": {"file_name": "file_path", "filename": "file_path", "path": "file_path"},
        "read_file_tool":   {"file_name": "file_path", "filename": "file_path", "path": "file_path"},
        "list_directory_tool": {"directory": "path", "dir": "path", "folder": "path"},
        "check_file_exists": {"file_name": "target", "filename": "target", "file": "target", "path": "target"},
    }

    async def run_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Universal tool execution with centralized logging."""
        import Tools
        
        # Normalize tool name
        tool_name = self._TOOL_ALIASES.get(tool_name, tool_name)

        if not hasattr(Tools, tool_name):
            log.tool_fail(tool_name, f"Tool not found in registry")
            return f"Error: Tool '{tool_name}' not found."

        tool_obj = getattr(Tools, tool_name)
        
        try:
            # 1. Normalize arguments
            final_args = tool_args.get("arguments", tool_args)
            aliases = self._ARG_ALIASES.get(tool_name, {})
            final_args = {aliases.get(k, k): v for k, v in final_args.items()}

            # Specialized logic for read_file_tool (relative paths)
            if tool_name == "read_file_tool":
                raw = final_args.get("file_path") or final_args.pop("file_name", None)
                if raw and not os.path.isabs(raw):
                    raw = os.path.join(get_workspace_dir(), raw)
                final_args["file_path"] = raw

            # 2. Log the call
            log.tool_call(tool_name, final_args)

            # 3. Execute
            if isinstance(tool_obj, BaseTool):
                result = await tool_obj.ainvoke(final_args)
            elif asyncio.iscoroutinefunction(tool_obj):
                result = await tool_obj(**final_args)
            else:
                result = tool_obj(**final_args)

            # 4. Log and return result
            res_str = str(result)
            log.tool_result(tool_name, res_str)
            log.tool_ok(tool_name, res_str[:100])
            
            return res_str

        except Exception as e:
            import traceback
            log.tool_fail(tool_name, str(e), exc=e)
            return f"Error executing tool '{tool_name}': {str(e)}\n{traceback.format_exc()}"

    def get_current_state(self) -> str:
        """
        Retrieves the current global state (e.g. tasks) to be injected into the prompt.
        """
        from config_loader import get_workspace_dir
        workspace = get_workspace_dir()
        task_file = os.path.join(workspace, ".agent_context/tasks.md")
        
        state = "\n\n[GLOBAL STATE / TASKS]\n"
        if os.path.exists(task_file):
            try:
                with open(task_file, "r", encoding="utf-8") as f:
                    state += f.read()
            except Exception as e:
                state += f"Error reading tasks: {e}"
        else:
            state += "No task list initialized."
            
        return state

    def _extract_json_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts tool calls from text that are formatted as JSON blocks or raw JSON objects.
        Supports various naming conventions for 'name' and 'arguments'.
        """
        extracted_calls = []
        # 1. Try to find JSON blocks first
        json_matches = re.findall(r"```json\n(.*?)\n```", text, re.DOTALL)
        if not json_matches:
            # 2. Try to find raw JSON objects if no blocks found
            json_matches = re.findall(r"(\{.*?\})", text, re.DOTALL)

        for json_str in json_matches:
            try:
                data = json.loads(json_str)
                # Handle list of calls or single call
                calls = data if isinstance(data, list) else [data]
                for call in calls:
                    if not isinstance(call, dict):
                        continue
                    
                    # Normalize 'name' field
                    name = call.get("name") or call.get("tool") or call.get("function") or call.get("action")
                    if not name:
                        continue
                        
                    # Normalize 'arguments' field
                    args = call.get("arguments") or call.get("args") or call.get("parameters") or call.get("params") or call.get("input")
                    if args is None:
                        # If no args field, assume the rest of the dict (excluding name field) are args
                        args = {k: v for k, v in call.items() if k not in ["name", "tool", "function", "action", "arguments", "args", "parameters", "params", "input"]}
                    
                    extracted_calls.append({
                        "name": str(name).strip(),
                        "arguments": args if isinstance(args, dict) else {}
                    })
            except json.JSONDecodeError:
                continue
        
        return extracted_calls

    def _generate_tool_docs(self, tool_names: List[str]) -> str:
        """Generates a detailed markdown documentation for the tools."""
        if not tool_names:
            return ""
            
        doc_str = "\n\n### [AVAILABLE TOOLS AND INPUT STRUCTURES]\n"
        available_tools = self._get_available_tools()
        
        for name in tool_names:
            if name in available_tools:
                tool_obj = available_tools[name]
                desc = tool_obj.description if hasattr(tool_obj, "description") else "No description available."
                
                # Try to get schema if it's a LangChain tool
                schema = ""
                if hasattr(tool_obj, "args_schema") and tool_obj.args_schema:
                    try:
                        schema_dict = tool_obj.args_schema.schema()
                        props = schema_dict.get("properties", {})
                        required = schema_dict.get("required", [])
                        schema_parts = []
                        for p_name, p_info in props.items():
                            req = "*" if p_name in required else ""
                            p_type = p_info.get("type", "string")
                            p_desc = p_info.get("description", "")
                            schema_parts.append(f"  - {p_name}{req} ({p_type}): {p_desc}")
                        schema = "\n".join(schema_parts)
                    except:
                        pass
                
                if not schema and hasattr(tool_obj, "func"):
                    # Fallback for simple tools
                    import inspect
                    sig = inspect.signature(tool_obj.func)
                    schema = "\n".join([f"  - {p_name}: {p_info.annotation if p_info.annotation != inspect.Parameter.empty else 'any'}" for p_name, p_info in sig.parameters.items()])

                doc_str += f"\n#### {name}\nDescription: {desc}\nArguments:\n{schema or '  - None'}\n"
        
        return doc_str
