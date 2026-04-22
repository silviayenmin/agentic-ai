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
            for tool_call in response.tool_calls:
                final_output += await self._run_tool(tool_call.name, tool_call.args)

        # 2. Tool calls embedded as JSON in text response
        elif response.content:
            content_text = response.content.strip()
            json_matches = re.findall(r"```json\n(.*?)\n```", content_text, re.DOTALL)
            if not json_matches:
                json_matches = re.findall(r"\{.*\"name\":.*\}", content_text, re.DOTALL)

            if json_matches:
                log.step(self.name, f"Found {len(json_matches)} JSON tool call(s) in text response")
                for json_str in json_matches:
                    try:
                        tool_data = json.loads(json_str)
                        if "name" in tool_data and "arguments" in tool_data:
                            final_output += await self._run_tool(tool_data["name"], tool_data["arguments"])
                    except json.JSONDecodeError as e:
                        log.warn(self.name, f"Could not parse JSON tool call: {e}")
                        continue

            if not final_output:
                log.warn(self.name, "No tool calls found — returning raw LLM text as output")
                final_output = response.content

        if not final_output:
            log.warn(self.name, "No actionable output or tools found")
            final_output = "No actionable output or tools found."

        log.agent_ok(self.name, f"Task complete. Output length: {len(final_output)} chars")
        self.memory.save_context({"input": full_input}, {"output": final_output})
        return final_output

    # Normalize argument keys that LLMs commonly get wrong.
    # Schema reference:
    #   create_file_tool → file_path  (relative, resolved under workspace)
    #   write_to_file    → file_name  (relative, resolved under workspace)
    #   read_file_tool   → file_path  (ABSOLUTE path required)
    _ARG_ALIASES: Dict[str, Dict[str, str]] = {
        "write_to_file":    {"file_path": "file_name", "filename": "file_name"},
        "create_file_tool": {"file_name": "file_path", "filename": "file_path"},
        # read_file_tool uses file_path but LLMs often pass file_name — handled below
    }

    async def _run_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        if not hasattr(Tools, tool_name):
            log.tool_fail(tool_name, f"Tool not found in Tools registry")
            return f"Error: Tool '{tool_name}' not found.\n"

        tool_obj = getattr(Tools, tool_name)
        try:
            # Unwrap nested 'arguments' key if the LLM wrapped its JSON that way
            final_args = tool_args.get("arguments", tool_args)

            # Normalize aliased argument names
            aliases = self._ARG_ALIASES.get(tool_name, {})
            final_args = {aliases.get(k, k): v for k, v in final_args.items()}

            # read_file_tool requires an ABSOLUTE file_path.
            # If the LLM gave a relative name, resolve it against the workspace dir.
            if tool_name == "read_file_tool":
                raw = final_args.get("file_path") or final_args.pop("file_name", None)
                if raw and not os.path.isabs(raw):
                    raw = os.path.join(get_workspace_dir(), raw)
                final_args["file_path"] = raw

            log.tool_call(tool_name, final_args)

            # StructuredTool objects (decorated with @tool) must use .ainvoke().
            from langchain_core.tools import BaseTool
            if isinstance(tool_obj, BaseTool):
                tool_result = await tool_obj.ainvoke(final_args)
            elif asyncio.iscoroutinefunction(tool_obj):
                tool_result = await tool_obj(**final_args)
            else:
                tool_result = tool_obj(**final_args)

            log.tool_ok(tool_name, str(tool_result)[:200])
            return f"Tool '{tool_name}' executed: {tool_result}\n"
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            log.tool_fail(tool_name, str(e), exc=e)
            return f"Error executing tool '{tool_name}': {str(e)}\n{tb}"
