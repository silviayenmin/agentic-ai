import asyncio
from langgraph.graph import StateGraph, END
from workflow.state import AgentState
from agents.analyzer.agent import AnalyzerAgent
from agents.dependency_checker.agent import DependencyCheckerAgent
from agents.planner.agent import PlannerAgent
from agents.executor.agent import ExecutorAgent
from agents.code_evaluator.agent import CodeEvaluatorAgent


async def analyzer_node(state: AgentState):
    agent = AnalyzerAgent()
    retry_count = state.get("retry_count", 0)
    res = await agent.analyze(state["input"], retry_count=retry_count)
    return {"analysis": res}


async def dependency_node(state: AgentState):
    agent = DependencyCheckerAgent()
    retry_count = state.get("retry_count", 0)
    res = await agent.check_dependencies(state["analysis"], retry_count=retry_count)
    return {"dependencies": res}


async def planner_node(state: AgentState):
    agent = PlannerAgent()
    retry_count = state.get("retry_count", 0)
    feedback = state.get("evaluation_feedback", "")
    res = await agent.plan(state["analysis"], feedback=feedback, retry_count=retry_count)
    return {"plan": res}


async def executor_node(state: AgentState):
    agent = ExecutorAgent()
    retry_count = state.get("retry_count", 0)
    res = await agent.execute_task("Implement the plan", context=state["plan"], retry_count=retry_count)
    return {"output": res}


async def code_evaluator_node(state: AgentState):
    agent = CodeEvaluatorAgent()
    retry_count = state.get("retry_count", 0)
    res = await agent.evaluate_code(state["input"], state["output"], retry_count=retry_count)
    # Check if the evaluation approves the code (Simple check for "APPROVED")
    is_valid = "APPROVED" in res.upper()
    
    new_retry_count = retry_count
    next_step = "FINISH" if is_valid else "RETRY"

    if not is_valid:
        new_retry_count += 1
        if new_retry_count >= 10:
            next_step = "FAIL"
        
    return {
        "evaluation_feedback": res, 
        "next_step": next_step,
        "retry_count": new_retry_count
    }


def build_coding_flow():
    workflow = StateGraph(AgentState)

    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("dependency", dependency_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("evaluator", code_evaluator_node)

    workflow.set_entry_point("analyzer")
    workflow.add_edge("analyzer", "dependency")
    workflow.add_edge("dependency", "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "evaluator")

    # Conditional routing: If not approved, go back to planner
    workflow.add_conditional_edges(
        "evaluator",
        lambda state: state["next_step"],
        {
            "FINISH": END, 
            "RETRY": "planner",
            "FAIL": END
        },
    )

    return workflow.compile()


if __name__ == "__main__":
    app = build_coding_flow()
    # with open("uigraph/coding_flow.png", "wb") as f:
    #     f.write(app.get_graph().draw_mermaid_png())
    initial_state = {
        "input": "Create a new FastAPI endpoint",
        "chat_history": [],
        "analysis": "",
        "plan": "",
        "dependencies": "",
        "output": "",
        "evaluation_feedback": "",
        "next_step": "",
        "retry_count": 0,
        "errors": [],
    }
    result = asyncio.run(app.ainvoke(initial_state))
    print("Standalone Coding Flow Test Result:", result)
