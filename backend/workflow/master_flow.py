from langgraph.graph import StateGraph, END
from workflow.state import AgentState
from agents.master.agent import MasterAgent
from workflow.chat_flow import build_chat_flow
from workflow.coding_flow import build_coding_flow

# Compile the sub-graphs
chat_flow = build_chat_flow()
coding_flow = build_coding_flow()

def master_router(state: AgentState):
    agent = MasterAgent()
    decision = asyncio.run(agent.route_query(state["input"]))
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
        {
            "CHAT": "chat_workflow",
            "CODING": "coding_workflow"
        }
    )
    
    workflow.add_edge("chat_workflow", END)
    workflow.add_edge("coding_workflow", END)
    
    return workflow.compile()

if __name__ == "__main__":
    import asyncio
    app = build_master_workflow()
    
    # Example test
    state = {"input": "Create a new file called demo.txt", "chat_history": []}
    result = app.invoke(state)
    print("Final State:", result)
