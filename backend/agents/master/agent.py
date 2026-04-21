import os
import json
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage


class MasterAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def route_query(self, user_input: str) -> dict:
        """
        Routes the user query to the appropriate category.
        """
        history = self.memory.load_memory_variables({})["chat_history"]
        
        # Enforce structured output via prompt instructions if not using bind_tools
        routing_instruction = (
            "Analyze the query and respond in ONLY valid JSON format: "
            "{\"category\": \"CHAT\" | \"CODING\", \"reason\": \"string\"}"
        )
        
        messages = [self.system_prompt] + history + [HumanMessage(content=f"{routing_instruction}\n\nQuery: {user_input}")]

        response = await self.llm.ainvoke(messages)
        self.memory.save_context({"input": user_input}, {"output": response.content})
        
        try:
            # Clean response in case the LLM adds markdown triple backticks
            clean_content = response.content.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_content)
        except json.JSONDecodeError:
            return {"category": "UNKNOWN", "content": response.content}
