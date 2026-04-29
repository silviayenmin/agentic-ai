import os
import re
import json
import asyncio
import sys
import subprocess
import uuid
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage
from typing import Dict, Any, List
from logger import log

# Import all available tools
import Tools
from config_loader import get_workspace_dir, get_workspace_name

class ExecutorAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def execute_task(self, task_description: str, context: str = "", retry_count: int = 0) -> str:
        """
        Executes a specific task by parsing the plan and calling the appropriate tools.
        Uses a multi-turn loop to refresh dynamic project context after each turn.
        """
        log.agent_start(self.name, task_description[:120])

        auto_context = ""
        analysis_path = ".agent_context/analysis.md"
        plan_path = ".agent_context/plan.md"
        dep_path = ".agent_context/dependencies.md"
        
        # Knowledge is in config/ for git tracking
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        knowledge_path = os.path.join(backend_dir, "config", "agent_knowledge.md")

        for label, path in [("analysis", analysis_path), ("dependencies", dep_path), ("plan", plan_path), ("knowledge", knowledge_path)]:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    auto_context += f"--- {label.upper()} ---\n{f.read()}\n\n"
                log.step(self.name, f"Loaded context file: {path}")

        full_input = f"{auto_context}Additional Context: {context}\n\nTask to Execute: {task_description}"
        # print("full_input ----------------------",full_input)
        # Start the message history with the user input
        messages = [HumanMessage(content=full_input)]
        
        from langchain_core.messages import SystemMessage, ToolMessage
        
        max_turns = 10
        turn = 0
        final_output = ""

        while turn < max_turns:
            turn += 1
            log.step(self.name, f"Starting execution turn {turn}/{max_turns}")
            
            # 1. GATHER REAL-TIME DYNAMIC CONTEXT
            structure = Tools.list_nested_directory.invoke({"path": "."})
            
            # Extract relevant files from the plan
            relevant_files = "Root project files"
            if os.path.exists(plan_path):
                try:
                    with open(plan_path, "r", encoding="utf-8") as f:
                        plan_text = f.read()
                        files = re.findall(r'[\w\-/]+\.\w+', plan_text)
                        if files:
                            relevant_files = ", ".join(list(set(files))[:10])
                except: pass
            
            # 2. REFRESH SYSTEM PROMPT with new knowledge
            from config_loader import get_workspace_name
            template = self.agent_config.get("system_prompt", "")
            workspace_name = get_workspace_name()
            formatted_prompt = template.replace("{project_structure}", str(structure)).replace("{relevant_files}", str(relevant_files)).replace("{workspace_name}", workspace_name)
            sys_msg = SystemMessage(content=formatted_prompt)
            
            # Construct current message list (System + History + Current Turn)
            history = self.memory.load_memory_variables({})["chat_history"]
            current_messages = [sys_msg] + history + messages
            
            # 3. INVOKE LLM
            response = await self.invoke_llm(current_messages, retry_count=retry_count)
            
            # Add AI response to turn messages
            messages.append(response)

            # 4. HANDLE TOOL CALLS
            has_executed_tools = False
            
            # A. Formal tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tc in response.tool_calls:
                    tc = tc if isinstance(tc, dict) else tc.dict()
                    tool_result = await self.run_tool(tc.get("name", ""), tc.get("args", {}))
                    final_output += tool_result
                    # Add ToolMessage to history for the next turn
                    messages.append(ToolMessage(tool_call_id=tc.get("id", str(uuid.uuid4())), content=tool_result))
                    has_executed_tools = True
            
            # B. JSON embedded tool calls
            else:
                json_calls = self._extract_json_tool_calls(response.content) if response.content else []
                if json_calls:
                    for tc in json_calls:
                        tool_result = await self.run_tool(tc["name"], tc["arguments"])
                        final_output += tool_result
                        # For JSON calls, we simulate a ToolMessage in text format
                        messages.append(HumanMessage(content=f"Tool '{tc['name']}' result: {tool_result}"))
                        has_executed_tools = True

            # 5. IF NO TOOLS EXECUTED, WE ARE DONE
            if not has_executed_tools:
                if response.content:
                    final_output = response.content
                break

        if not final_output:
            final_output = "No actionable output or tools found."

        log.agent_ok(self.name, f"Multi-turn execution complete ({turn} turns).")
        self.memory.save_context({"input": full_input}, {"output": final_output})
        return final_output
