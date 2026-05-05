from langgraph.graph import StateGraph, END
from workflow.state import AgentState
from agents.master.agent import MasterAgent
from workflow.chat_flow import build_chat_flow
from workflow.coding_flow import build_coding_flow
from logger import log

# Compile the sub-graphs
chat_flow = build_chat_flow()
coding_flow = build_coding_flow()


async def master_router(state: AgentState):
    log.info("Master", "Analyzing query for routing...")
    agent = MasterAgent()
    agent.set_chat_history(state.get("chat_history", []))
    decision = await agent.route_query(state["input"])
    
    category = decision.get("category", "CHAT")
    log.route("Master", category, decision.get("reason", "No reason provided"))
    
    # We add the user input and the routing decision to history
    new_history = [f"User: {state['input']}", f"Master: Routed to {category}"]
    
    # Check for bypass keywords
    lower_input = state["input"].lower()
    is_bypass = "bypass" in lower_input or "existing" in lower_input
    
    use_existing_analysis = False
    use_existing_plan = False

    if is_bypass:
        if "analysis" in lower_input and "plan" not in lower_input:
            use_existing_analysis = True
        elif "plan" in lower_input and "analysis" not in lower_input:
            use_existing_plan = True
        else:
            # Default to both if not specified or both mentioned
            use_existing_analysis = True
            use_existing_plan = True

    return {
        "next_step": category, 
        "retry_count": 0,
        "chat_history": new_history,
        "use_existing_analysis": use_existing_analysis,
        "use_existing_plan": use_existing_plan
    }


async def fallback_node(state: AgentState):
    log.warn("Master", "Workflow has entered FALLBACK mode due to terminal failure in sub-workflow.")
    log.info("Master", f"Accumulated Errors: {state.get('errors', [])}")
    
    # We could trigger a specialized "Fixer" agent here, 
    # but for now we provide a detailed failure report.
    failure_report = f"TERMINAL FAILURE: Workflow exhausted all retries.\nLast Error: {state.get('errors', ['Unknown error'])[-1]}"
    
    return {"output": failure_report, "chat_history": ["System: Entered Fallback mode."]}


def build_master_workflow():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("master", master_router)
    workflow.add_node("chat_workflow", chat_flow)
    workflow.add_node("coding_workflow", coding_flow)
    workflow.add_node("fallback", fallback_node)

    # Logic for routing
    workflow.set_entry_point("master")

    # Conditional routing for master
    workflow.add_conditional_edges(
        "master",
        lambda state: state["next_step"],
        {"CHAT": "chat_workflow", "CODING": "coding_workflow", "UNKNOWN": "chat_workflow"},
    )

    # Sub-workflow completion edges
    workflow.add_edge("chat_workflow", END)
    
    # Conditional routing for coding failure
    workflow.add_conditional_edges(
        "coding_workflow",
        lambda state: "RETRY" if state.get("next_step") == "FAIL" else "END",
        {"RETRY": "fallback", "END": END}
    )

    workflow.add_edge("fallback", END)

    return workflow.compile()


if __name__ == "__main__":
    import asyncio

    app = build_master_workflow()

    # with open("uigraph/master_flow.png", "wb") as f:
    #     f.write(app.get_graph().draw_mermaid_png())

    message = input("Query : ")

    # Example test
    state = {
        "input": message,
        "chat_history": [],
    }
    
    result = asyncio.run(app.ainvoke(state))
    
    print("\n" + "="*60)
    print("             AGENTIC WORKFLOW FINAL SUMMARY")
    print("="*60)
    
    print(f"\n[FINAL OUTPUT]\n{result.get('output', 'No final output recorded.')}")
    
    if result.get("errors"):
        print("\n[ERRORS ENCOUNTERED]")
        for err in result["errors"]:
            print(f"  ❌ {err}")
            
    print("\n[CHAT & LOG HISTORY]")
    for entry in result.get('chat_history', []):
        # Print first line or first 150 chars
        summary = entry.split('\n')[0]
        if len(summary) > 150: summary = summary[:147] + "..."
        print(f"  • {summary}")
        
    print("\n" + "="*60)
