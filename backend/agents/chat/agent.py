import os
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage


class ChatAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def chat(self, user_input: str) -> str:
        history = self.memory.load_memory_variables({})["chat_history"]
        messages = [self.system_prompt] + history + [HumanMessage(content=user_input)]

        response = await self.invoke_llm(messages)
        self.memory.save_context({"input": user_input}, {"output": response.content})
        return response.content


# if __name__ == "__main__":
#     import asyncio
#     async def test():
#         agent = ChatAgent()
#         print(f"Starting {agent.name}...")
#         res = await agent.chat("What can you do?")
#         print(f"AI: {res}")

#     asyncio.run(test())
