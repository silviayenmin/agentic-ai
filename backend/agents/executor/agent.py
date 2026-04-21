import os
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage


class ExecutorAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def execute_task(self, task_description: str, context: str = "") -> str:
        """
        Executes a specific task. Automatically pulls context from .agent_context if available.
        """
        # Automatically load context from files
        auto_context = ""
        analysis_path = ".agent_context/analysis.md"
        plan_path = ".agent_context/plan.md"
        dep_path = ".agent_context/dependencies.md"

        if os.path.exists(analysis_path):
            with open(analysis_path, "r", encoding="utf-8") as f:
                auto_context += f"--- ANALYSIS ---\n{f.read()}\n\n"
        
        if os.path.exists(dep_path):
            with open(dep_path, "r", encoding="utf-8") as f:
                auto_context += f"--- DEPENDENCIES ---\n{f.read()}\n\n"

        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                auto_context += f"--- PLAN ---\n{f.read()}\n\n"

        full_input = f"{auto_context}Additional Context: {context}\n\nTask to Execute: {task_description}"
        
        history = self.memory.load_memory_variables({})["chat_history"]
        messages = [self.system_prompt] + history + [HumanMessage(content=full_input)]

        response = await self.llm.ainvoke(messages)
        self.memory.save_context({"input": full_input}, {"output": response.content})
        return response.content
