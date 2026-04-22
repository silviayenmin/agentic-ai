import os
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage


class ChatEvaluatorAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def evaluate(self, user_request: str, proposed_response: str) -> str:
        """
        Evaluates a proposed response against the original user request.
        """
        evaluation_input = f"User Request: {user_request}\n\nProposed Response: {proposed_response}"
        
        history = self.memory.load_memory_variables({})["chat_history"]
        messages = [self.system_prompt] + history + [HumanMessage(content=evaluation_input)]

        response = await self.invoke_llm(messages)
        self.memory.save_context({"input": evaluation_input}, {"output": response.content})
        return response.content
