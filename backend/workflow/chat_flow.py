import asyncio
from langgraph.graph import StateGraph, END
from workflow.state import AgentState
from agents.chat.agent import ChatAgent
from agents.chat_evaluator.agent import ChatEvaluatorAgent


async def chat_node(state: AgentState):
    agent = ChatAgent()
    response = await agent.chat(state["input"])
    return {"output": response}


async def chat_evaluator_node(state: AgentState):
    evaluator = ChatEvaluatorAgent()
    feedback = await evaluator.evaluate(state["input"], state["output"])
    return {"evaluation_feedback": feedback}


def build_chat_flow():
    workflow = StateGraph(AgentState)

    workflow.add_node("chat", chat_node)
    workflow.add_node("evaluator", chat_evaluator_node)

    workflow.set_entry_point("chat")
    workflow.add_edge("chat", "evaluator")
    workflow.add_edge("evaluator", END)

    return workflow.compile()


if __name__ == "__main__":
    app = build_chat_flow()
    # with open("uigraph/chat_flow.png", "wb") as f:
    #     f.write(app.get_graph().draw_mermaid_png())
    initial_state = {"input": "Hello, how are you?", "chat_history": []}
    result = asyncio.run(app.ainvoke(initial_state))
    print(result)
