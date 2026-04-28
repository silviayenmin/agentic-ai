import os
import re
import json
import asyncio
import sys
import subprocess
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage
from typing import Dict, Any, List
from logger import log

# Import all available tools
import Tools
from config_loader import get_workspace_dir

class ExecutorAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def execute_task(self, task_description: str, context: str = "", retry_count: int = 0) -> str:
        """
        Executes a specific task by parsing the plan and calling the appropriate tools.
        """
        log.agent_start(self.name, task_description[:120])

        auto_context = ""
        analysis_path = ".agent_context/analysis.md"
        plan_path = ".agent_context/plan.md"
        dep_path = ".agent_context/dependencies.md"

        for label, path in [("analysis", analysis_path), ("dependencies", dep_path), ("plan", plan_path)]:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    auto_context += f"--- {label.upper()} ---\n{f.read()}\n\n"
                log.step(self.name, f"Loaded context file: {path}")

        full_input = f"{auto_context}Additional Context: {context}\n\nTask to Execute: {task_description}"

        history = self.memory.load_memory_variables({})["chat_history"]
        messages = [self.system_prompt] + history + [HumanMessage(content=full_input)]

        response = await self.invoke_llm(messages, retry_count=retry_count)

        final_output = ""

        # 1. Formal tool_calls from LLM
        if hasattr(response, 'tool_calls') and response.tool_calls:
            log.step(self.name, f"Dispatching {len(response.tool_calls)} formal tool call(s)")
            for tc in response.tool_calls:
                tc = tc if isinstance(tc, dict) else tc.dict()
                tool_result = await self.run_tool(tc.get("name", ""), tc.get("args", {}))
                final_output += tool_result

        # 2. Tool calls embedded as JSON in text response
        elif response.content:
            content_text = response.content.strip()
            json_calls = self._extract_json_tool_calls(content_text)
            if json_calls:
                log.step(self.name, f"Found {len(json_calls)} JSON tool call(s) in text response")
                for tc in json_calls:
                    tool_result = await self.run_tool(tc["name"], tc["arguments"])
                    final_output += tool_result

            if not final_output:
                log.warn(self.name, "No tool calls found — returning raw LLM text as output")
                final_output = response.content

        if not final_output:
            log.warn(self.name, "No actionable output or tools found")
            final_output = "No actionable output or tools found."

        log.agent_ok(self.name, f"Task complete. Output length: {len(final_output)} chars")
        self.memory.save_context({"input": full_input}, {"output": final_output})
        return final_output
