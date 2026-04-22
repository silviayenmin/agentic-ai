import asyncio
from langgraph.graph import StateGraph, END
from workflow.state import AgentState
from agents.master.agent import MasterAgent
from workflow.chat_flow import build_chat_flow
from workflow.coding_flow import build_coding_flow

# Compile the sub-graphs
chat_flow = build_chat_flow()
coding_flow = build_coding_flow()


async def master_router(state: AgentState):
    agent = MasterAgent()
    decision = await agent.route_query(state["input"])
    return {"next_step": decision.get("category", "CHAT")}


def build_master_workflow():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("master", master_router)
    workflow.add_node("chat_workflow", chat_flow)
    workflow.add_node("coding_workflow", coding_flow)

    # Logic for routing
    workflow.set_entry_point("master")

    # Conditional routing based on next_step
    workflow.add_conditional_edges(
        "master",
        lambda state: state["next_step"],
        {"CHAT": "chat_workflow", "CODING": "coding_workflow"},
    )

    workflow.add_edge("chat_workflow", END)
    workflow.add_edge("coding_workflow", END)

    return workflow.compile()


if __name__ == "__main__":
    app = build_master_workflow()

    # with open("uigraph/master_flow.png", "wb") as f:
    #     f.write(app.get_graph().draw_mermaid_png())

    # Example test
    state = {"input": "Create a new file called demo.txt", "chat_history": []}
    result = asyncio.run(app.ainvoke(state))
    print("Final State:", result)
