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
        
        final_output = ""
        # 1. Formal tool_calls from LLM
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tc in response.tool_calls:
                tc = tc if isinstance(tc, dict) else tc.dict()
                tool_result = await self.run_tool(tc.get("name", ""), tc.get("args", {}))
                final_output += f"\n[Tool Result: {tc.get('name')}]\n{tool_result}"
        
        # 2. Text response
        if response.content:
            final_output = response.content + ("\n" + final_output if final_output else "")

        self.memory.save_context({"input": user_input}, {"output": final_output})
        return final_output


# if __name__ == "__main__":
#     import asyncio
#     async def test():
#         agent = ChatAgent()
#         print(f"Starting {agent.name}...")
#         res = await agent.chat("What can you do?")
#         print(f"AI: {res}")

#     asyncio.run(test())
