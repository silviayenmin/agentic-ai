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
            import Tools
            available_tools = {
                "check_file_permissions": Tools.check_file_permissions,
                "request_os_permission": Tools.request_os_permission,
                "execute_command": Tools.execute_command,
                "stop_process": Tools.stop_process,
                "read_file": Tools.read_file,
                "write_file": Tools.write_file_tool,
                "find_file": Tools.find_file,
                "search_code": Tools.search_code,
                "check_file_exists": Tools.check_file_exists,
                "web_search": Tools.web_search_tool,
                "create_file": Tools.create_file,
            }
            return [available_tools[name] for name in tool_names if name in available_tools]
        except ImportError as e:
            print(f"[BaseAgent] Error loading tools: {e}")
            return []
