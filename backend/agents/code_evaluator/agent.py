import os
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage


class CodeEvaluatorAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def evaluate_code(self, user_request: str, proposed_code: str) -> str:
        """
        Technical evaluation of proposed code.
        """
        evaluation_input = f"User Request: {user_request}\n\nProposed Code Changes:\n{proposed_code}"
        
        history = self.memory.load_memory_variables({})["chat_history"]
        messages = [self.system_prompt] + history + [HumanMessage(content=evaluation_input)]

        response = await self.llm.ainvoke(messages)
        self.memory.save_context({"input": evaluation_input}, {"output": response.content})
        return response.content
