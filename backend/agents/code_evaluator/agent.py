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

            # 1. Formal tool calls — execute and feed results back
            if hasattr(response, "tool_calls") and response.tool_calls:
                from langchain_core.messages import ToolMessage
                log.step(self.name, f"Executing {len(response.tool_calls)} evaluator tool call(s)")
                messages.append(response)
                for tc in response.tool_calls:
                    result = await self.run_tool(tc.get("name", ""), tc.get("args", {}))
                    messages.append(
                        ToolMessage(content=str(result), tool_call_id=tc["id"])
                    )
                continue

            # 2. Tool calls embedded as JSON in text response (Fallback)
            elif response.content:
                content_text = response.content.strip()
                import re
                import json
                # Look for ```json ... ``` or a raw JSON object
                json_matches = re.findall(r"```json\n(.*?)\n```", content_text, re.DOTALL)
                if not json_matches:
                    json_matches = re.findall(r"\{.*\"name\":.*\}", content_text, re.DOTALL)

                if json_matches:
                    log.step(self.name, f"Found {len(json_matches)} JSON block(s) in text response")
                    processed_any = False
                    for json_str in json_matches:
                        try:
                            tool_data = json.loads(json_str)
                            calls = tool_data if isinstance(tool_data, list) else [tool_data]
                            for tc in calls:
                                import uuid
                                call_id = f"json_{uuid.uuid4().hex[:8]}"
                                result = await self.run_tool(tc["name"], tc["arguments"])
                                messages.append(response) # Add the assistant message
                                from langchain_core.messages import ToolMessage
                                messages.append(ToolMessage(content=str(result), tool_call_id=call_id))
                                processed_any = True
                        except json.JSONDecodeError:
                            continue
                    
                    if processed_any:
                        continue # Go to next round after processing JSON tools

                # 3. Plain text verdict (only if no tool calls found above)
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

            log.warn(self.name, f"Round {round_num}: no content and no tool calls — breaking loop")
            break

        fallback = "Evaluation inconclusive after tool rounds. Please review output manually."
        log.agent_fail(self.name, "Evaluation inconclusive after all tool rounds")
        self.memory.save_context({"input": evaluation_input}, {"output": fallback})
        return fallback

