import os
import json
import sys
from typing import Dict, Any, List
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langchain_classic.memory import ConversationBufferMemory
from dotenv import load_dotenv
from logger import log

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
        import asyncio
        last_error = None
        workflow_attempt = retry_count + 1

        for attempt in range(1, max_retries + 1):
            try:
                log.llm_call(self.name, attempt, workflow_attempt)

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

    def _load_tools(self, tool_names: List[str]):
        try:
            import Tools
            available_tools = {
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
            }
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
