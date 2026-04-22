import asyncio
from langgraph.graph import StateGraph, END
from workflow.state import AgentState
from agents.chat.agent import ChatAgent
from agents.chat_evaluator.agent import ChatEvaluatorAgent
from logger import log
 
 
async def chat_node(state: AgentState):
    log.info("ChatFlow", "Entering Chat node")
    agent = ChatAgent()
    agent.set_chat_history(state.get("chat_history", []))
    response = await agent.chat(state["input"])
    return {"output": response, "chat_history": [f"ChatAgent: {response}"]}
 
 
async def chat_evaluator_node(state: AgentState):
    log.info("ChatFlow", "Entering Chat Evaluator node")
    evaluator = ChatEvaluatorAgent()
    evaluator.set_chat_history(state.get("chat_history", []))
    feedback = await evaluator.evaluate(state["input"], state["output"])
    log.agent_ok("ChatFlow", "Evaluation complete")
    return {"evaluation_feedback": feedback, "chat_history": [f"ChatEvaluator: {feedback}"]}
 
 
def build_chat_flow():
    workflow = StateGraph(AgentState)
 
    workflow.add_node("chat", chat_node)
    workflow.add_node("evaluator", chat_evaluator_node)
 
    workflow.set_entry_point("chat")
    workflow.add_edge("chat", "evaluator")
    # workflow.add_conditional_edges(
    #     "evaluator",
    #     lambda state: state["next_step"],
    #     {"CHAT": "chat", "CODING": "coding_workflow"},
    # )
    workflow.add_edge("evaluator", END)
 
    return workflow.compile()
 
 
if __name__ == "__main__":
    import asyncio
 
    app = build_chat_flow()
    # with open("uigraph/chat_flow.png", "wb") as f:
    #     f.write(app.get_graph().draw_mermaid_png())
    initial_state = {"input": "Hello, how are you?", "chat_history": []}
    result = asyncio.run(app.ainvoke(initial_state))
    print(result)
 
 