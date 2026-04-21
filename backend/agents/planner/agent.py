import os
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage


class PlannerAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def plan(self, analysis_input: str) -> str:
        """
        Takes the analysis from the Analyzer agent and splits it into tasks.
        """
        history = self.memory.load_memory_variables({})["chat_history"]
        messages = [self.system_prompt] + history + [HumanMessage(content=analysis_input)]

        response = await self.llm.ainvoke(messages)
        self.memory.save_context({"input": analysis_input}, {"output": response.content})
        
        # New feature: Save the plan for the Executor
        plan_path = ".agent_context/plan.md"
        os.makedirs(os.path.dirname(plan_path), exist_ok=True)
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(response.content)
            
        return response.content
