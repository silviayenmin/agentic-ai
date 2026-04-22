import os
import asyncio
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage
from logger import log


class CodeEvaluatorAgent(BaseAgent):
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def evaluate_code(self, user_request: str, proposed_code: str, retry_count: int = 0) -> str:
        """
        Technical evaluation of proposed code.

        Runs an agentic loop so any tool calls the LLM makes (e.g. check_file_exists,
        read_file) are executed and fed back as ToolMessages before a final
        APPROVED / rejection text verdict is returned.
        """
        log.agent_start(self.name, f"Evaluating output for: {user_request[:80]}")

        evaluation_input = (
            f"User Request: {user_request}\n\nProposed Code Changes:\n{proposed_code}"
        )

        history = self.memory.load_memory_variables({})["chat_history"]
        messages = [self.system_prompt] + history + [HumanMessage(content=evaluation_input)]

        MAX_TOOL_ROUNDS = 5
        for round_num in range(1, MAX_TOOL_ROUNDS + 1):
            log.step(self.name, f"Evaluation round {round_num}/{MAX_TOOL_ROUNDS}")
            response = await self.invoke_llm(messages, retry_count=retry_count)

            # Plain text verdict — we're done
            if response.content and response.content.strip():
                verdict = response.content.strip()
                is_approved = "APPROVED" in verdict.upper()
                if is_approved:
                    log.agent_ok(self.name, "Verdict: APPROVED ✅")
                else:
                    log.agent_fail(self.name, f"Verdict: REJECTED — {verdict[:120]}")
                self.memory.save_context(
                    {"input": evaluation_input}, {"output": verdict}
                )
                return verdict

            # Formal tool calls — execute and feed results back
            if hasattr(response, "tool_calls") and response.tool_calls:
                from langchain_core.messages import ToolMessage
                log.step(self.name, f"Executing {len(response.tool_calls)} evaluator tool call(s)")
                messages.append(response)

                for tc in response.tool_calls:
                    result = await self._execute_tool(
                        tc.get("name", ""), tc.get("args", {})
                    )
                    messages.append(
                        ToolMessage(content=str(result), tool_call_id=tc["id"])
                    )
                continue

            log.warn(self.name, f"Round {round_num}: no content and no tool calls — breaking loop")
            break

        fallback = "Evaluation inconclusive after tool rounds. Please review output manually."
        log.agent_fail(self.name, "Evaluation inconclusive after all tool rounds")
        self.memory.save_context({"input": evaluation_input}, {"output": fallback})
        return fallback

    async def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """Executes a single bound tool and returns its result as a string."""
        import Tools
        from langchain_core.tools import BaseTool

        # Resolve short aliases used in config.json → real exported names
        _ALIASES = {
            "read_file": "read_file_tool",
            "write_file": "write_to_file",
            "create_file": "create_file_tool",
        }
        resolved = _ALIASES.get(tool_name, tool_name)

        if not hasattr(Tools, resolved):
            return f"Tool '{tool_name}' not found."

        tool_obj = getattr(Tools, resolved)
        try:
            if isinstance(tool_obj, BaseTool):
                return str(await tool_obj.ainvoke(tool_args))
            elif asyncio.iscoroutinefunction(tool_obj):
                return str(await tool_obj(**tool_args))
            else:
                return str(tool_obj(**tool_args))
        except Exception as e:
            return f"Tool error ({tool_name}): {e}"
