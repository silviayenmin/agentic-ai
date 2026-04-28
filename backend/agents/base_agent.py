import os
import json
from typing import Dict, Any, List
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langchain_classic.memory import ConversationBufferMemory
from dotenv import load_dotenv
 
load_dotenv()
 
class BaseAgent:
    def __init__(self, agent_dir: str, global_config_path: str = "config.json"):
        self.agent_dir = agent_dir
        self.global_config = self._load_json(global_config_path)
        self.agent_config = self._load_json(os.path.join(agent_dir, "config.json"))
       
        self.name = self.agent_config.get("name", "Unknown Agent")
        self.description = self.agent_config.get("description", "")
       
        self.llm = self._init_llm()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.system_prompt = SystemMessage(content=self.agent_config.get("system_prompt", ""))
 
    def _load_json(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            return json.load(f)
 
    def _init_llm(self):
        # 1. Determine which provider to use
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
                temperature=config.get("temperature", 0),
                headers={"X-Tunnel-Skip-Anti-Phishing-Page": "true"}
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
 
    def _load_tools(self, tool_names: List[str]):
        try:
            import tools as Tools
            available_tools = {
                "check_file_permissions": getattr(Tools, "check_file_permissions", None),
                "request_os_permission": getattr(Tools, "request_os_permission", None),
                "execute_command": getattr(Tools, "execute_command", None),
                "stop_process": getattr(Tools, "stop_process", None),
                "read_file": getattr(Tools, "read_file_tool", None),
                "read_file_tool": getattr(Tools, "read_file_tool", None),
                "write_file": getattr(Tools, "write_to_file", None),
                "write_to_file": getattr(Tools, "write_to_file", None),
                "find_file": getattr(Tools, "find_file", None),
                "search_code": getattr(Tools, "search_code", None),
                "check_file_exists": getattr(Tools, "check_file_exists", None),
                "web_search": getattr(Tools, "web_search_tool", None),
                "create_file": getattr(Tools, "create_file_tool", None),
                "create_file_tool": getattr(Tools, "create_file_tool", None),
                "list_directory": getattr(Tools, "list_directory_tool", None),
                "delete_file": getattr(Tools, "delete_file_tool", None),
                "update_task_status": getattr(Tools, "update_task_status", None),
                "get_task_list": getattr(Tools, "get_task_list", None),
            }

            return [available_tools[name] for name in tool_names if name in available_tools and available_tools[name] is not None]
        except Exception:
            return []

    # Normalize argument keys that LLMs commonly get wrong.
    _ARG_ALIASES: Dict[str, Dict[str, str]] = {
        "write_to_file":    {"file_path": "file_name", "filename": "file_name"},
        "create_file_tool": {"file_name": "file_path", "filename": "file_path"},
    }

    async def run_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Universal tool execution with centralized logging."""
        import tools as Tools
        from langchain_core.tools import BaseTool
        from config_loader import get_workspace_dir
        import asyncio

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
