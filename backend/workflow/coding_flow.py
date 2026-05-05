import asyncio
from langgraph.graph import StateGraph, END
from workflow.state import AgentState
from agents.analyzer.agent import AnalyzerAgent
from agents.dependency_checker.agent import DependencyCheckerAgent
from agents.planner.agent import PlannerAgent
from agents.executor.agent import ExecutorAgent
from agents.code_evaluator.agent import CodeEvaluatorAgent
from logger import log


def get_project_map(workspace_dir: str) -> str:
    """Generates a simple text-based map of the project structure."""
    import os
    project_map = []
    for root, dirs, files in os.walk(workspace_dir):
        # Skip hidden folders and node_modules
        if "node_modules" in root or ".git" in root or ".agent_context" in root:
            continue
        level = root.replace(workspace_dir, '').count(os.sep)
        indent = ' ' * 4 * (level)
        project_map.append(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            project_map.append(f"{sub_indent}{f}")
    return "\n".join(project_map)


async def analyzer_node(state: AgentState):
    log.info("CodingFlow", f"Starting analysis of user request: {state['input'][:50]}...")
    
    # Load existing context if it exists
    import os
    existing_analysis = ""
    if os.path.exists(".agent_context/analysis.md"):
        with open(".agent_context/analysis.md", "r", encoding="utf-8") as f:
            existing_analysis = f.read()

    # Bypass Check (Keep this for manual override)
    if state["input"].strip().upper().startswith("BYPASS"):
        log.info("CodingFlow", "Bypass mode detected. Loading existing analysis.md...")
        return {"analysis": existing_analysis, "chat_history": ["System: Bypass mode - loaded analysis from file"]}

    agent = AnalyzerAgent()
    agent.set_chat_history(state.get("chat_history", []))
    
    # Generate a map of the current project structure
    from config_loader import get_workspace_dir
    project_map = get_project_map(get_workspace_dir())
    
    # Pass both new input and existing context
    prompt = f"CURRENT PROJECT STRUCTURE:\n{project_map}\n\nUSER REQUEST: {state['input']}"
    if existing_analysis:
        prompt = f"EXISTING ANALYSIS:\n{existing_analysis}\n\n{prompt}\n\nUpdate the analysis by adding the new task. Maintain the inventory. USE ONLY REAL PATHS FROM THE STRUCTURE ABOVE."
    
    retry_count = state.get("retry_count", 0)
    res = await agent.analyze(prompt, retry_count=retry_count)
    log.step("Analyzer", "Requirements analysis complete (Incremental).")
    return {"analysis": res, "chat_history": [f"Analyzer: {res}"]}


async def dependency_node(state: AgentState):
    log.info("CodingFlow", "Checking system and project dependencies...")
    
    # Load existing context
    import os
    existing_deps = ""
    if os.path.exists(".agent_context/dependencies.md"):
        with open(".agent_context/dependencies.md", "r", encoding="utf-8") as f:
            existing_deps = f.read()

    # Bypass Check
    if state["input"].strip().upper().startswith("BYPASS"):
        log.info("CodingFlow", "Bypass mode - skipping dependency check.")
        return {"dependencies": existing_deps, "chat_history": ["System: Bypass mode - skipped dependency check"]}

    agent = DependencyCheckerAgent()
    agent.set_chat_history(state.get("chat_history", []))
    
    # Combine analysis with existing dependencies
    prompt = f"NEW ANALYSIS:\n{state['analysis']}"
    if existing_deps:
        prompt = f"EXISTING DEPENDENCIES:\n{existing_deps}\n\n{prompt}\n\nUpdate the dependency report with any new requirements while keeping the existing ones."

    retry_count = state.get("retry_count", 0)
    res = await agent.check_dependencies(prompt, retry_count=retry_count)
    log.step("DependencyChecker", "Dependency report updated (Incremental).")
    return {"dependencies": res, "chat_history": [f"Dependency Checker: {res}"]}


async def planner_node(state: AgentState):
    feedback = state.get("evaluation_feedback", "")
    
    # Load existing context
    import os
    existing_plan = ""
    if os.path.exists(".agent_context/plan.md"):
        with open(".agent_context/plan.md", "r", encoding="utf-8") as f:
            existing_plan = f.read()

    # STRICT Bypass Check: Never let the AI overwrite a manual plan
    if state["input"].strip().upper().startswith("BYPASS"):
        log.info("CodingFlow", "Bypass mode active. Refusing to overwrite manual plan.md.")
        return {"plan": existing_plan, "chat_history": ["System: Bypass mode - locked to manual plan.md"]}

    from config_loader import get_workspace_dir
    project_map = get_project_map(get_workspace_dir())
    
    if feedback:
        log.info("CodingFlow", "Re-planning based on evaluator feedback...")
        prompt = f"PROJECT STRUCTURE:\n{project_map}\n\nEXISTING PLAN:\n{existing_plan}\n\nFEEDBACK:\n{feedback}\n\nUpdate the plan to resolve the feedback. USE REAL PATHS ONLY."
    else:
        log.info("CodingFlow", "Updating implementation plan...")
        if existing_plan:
            prompt = f"PROJECT STRUCTURE:\n{project_map}\n\nEXISTING PLAN:\n{existing_plan}\n\nNEW ANALYSIS:\n{state['analysis']}\n\nAppend the new tasks. USE REAL PATHS ONLY."
        else:
            prompt = f"PROJECT STRUCTURE:\n{project_map}\n\nANALYSIS:\n{state['analysis']}\n\nCreate a plan using REAL PATHS ONLY."
        
    agent = PlannerAgent()
    agent.set_chat_history(state.get("chat_history", []))
    retry_count = state.get("retry_count", 0)
    res = await agent.plan(prompt, feedback=feedback, retry_count=retry_count)
    log.step("Planner", "Technical plan updated (Incremental).")
    return {"plan": res, "chat_history": [f"Planner: {res}"]}


async def executor_node(state: AgentState):
    log.info("CodingFlow", "Executing technical plan and applying changes...")
    agent = ExecutorAgent()
    agent.set_chat_history(state.get("chat_history", []))
    retry_count = state.get("retry_count", 0)
    res = await agent.execute_task("Implement the plan", context=state["plan"], retry_count=retry_count)
    log.step("Executor", "Plan execution finished.")
    return {"output": res, "chat_history": [f"Executor: {res}"]}


async def code_evaluator_node(state: AgentState):
    log.info("CodingFlow", "Evaluating output for quality and requirements compliance...")
    agent = CodeEvaluatorAgent()
    agent.set_chat_history(state.get("chat_history", []))
    retry_count = state.get("retry_count", 0)
    res = await agent.evaluate_code(state["input"], state["output"], retry_count=retry_count)
    # Check if the evaluation approves the code (Simple check for "APPROVED")
    is_valid = "APPROVED" in res.upper()
    
    new_retry_count = retry_count
    next_step = "FINISH" if is_valid else "RETRY"
    errors = []

    if not is_valid:
        new_retry_count += 1
        log.warn("CodingFlow", f"Code REJECTED by Evaluator (Attempt {new_retry_count}/10)")
        errors.append(f"Evaluation failed: {res}")
        
        if new_retry_count >= 10:
            log.agent_fail("CodingFlow", "Max retries (10) reached. Workflow failing.")
            next_step = "FAIL"
        else:
            log.route("Evaluator", "Planner", "Going back to Planner to resolve issues")
    else:
        log.agent_ok("CodingFlow", "Code APPROVED by Evaluator")
        log.route("Evaluator", "END", "Goal achieved")
        
    return {
        "evaluation_feedback": res, 
        "next_step": next_step,
        "retry_count": new_retry_count,
        "chat_history": [f"Evaluator: {res}"],
        "errors": errors
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
