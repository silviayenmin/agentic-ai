import os
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage


class AnalyzerAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def analyze(self, user_input: str, retry_count: int = 0) -> str:
        history = self.memory.load_memory_variables({})["chat_history"]
        messages = [self.system_prompt] + history + [HumanMessage(content=user_input)]

        response = await self.invoke_llm(messages, retry_count=retry_count)
        self.memory.save_context({"input": user_input}, {"output": response.content})
        
        # New feature: Save the analysis for the Planner/Executor
        analysis_path = ".agent_context/analysis.md"
        os.makedirs(os.path.dirname(analysis_path), exist_ok=True)
        with open(analysis_path, "w", encoding="utf-8") as f:
            f.write(response.content)
            
        return response.content
