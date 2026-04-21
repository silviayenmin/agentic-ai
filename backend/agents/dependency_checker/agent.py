import os
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage


class DependencyCheckerAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def check_dependencies(self, query: str) -> str:
        """
        Analyzes dependencies and saves the report to .agent_context/dependencies.md.
        """
        history = self.memory.load_memory_variables({})["chat_history"]
        messages = [self.system_prompt] + history + [HumanMessage(content=query)]

        response = await self.llm.ainvoke(messages)
        self.memory.save_context({"input": query}, {"output": response.content})
        
        # New feature: Save dependency report
        dep_path = ".agent_context/dependencies.md"
        os.makedirs(os.path.dirname(dep_path), exist_ok=True)
        with open(dep_path, "w", encoding="utf-8") as f:
            f.write(response.content)
            
        return response.content
