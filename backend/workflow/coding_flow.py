import asyncio
from langgraph.graph import StateGraph, END
from workflow.state import AgentState
from agents.analyzer.agent import AnalyzerAgent
from agents.dependency_checker.agent import DependencyCheckerAgent
from agents.planner.agent import PlannerAgent
from agents.executor.agent import ExecutorAgent
from agents.code_evaluator.agent import CodeEvaluatorAgent

def analyzer_node(state: AgentState):
    agent = AnalyzerAgent()
    res = asyncio.run(agent.analyze(state["input"]))
    return {"analysis": res}

def dependency_node(state: AgentState):
    agent = DependencyCheckerAgent()
    res = asyncio.run(agent.check_dependencies(state["analysis"]))
    return {"dependencies": res}

def planner_node(state: AgentState):
    agent = PlannerAgent()
    res = asyncio.run(agent.plan(state["analysis"]))
    return {"plan": res}

def executor_node(state: AgentState):
    agent = ExecutorAgent()
    res = asyncio.run(agent.execute_task("Implement the plan", context=state["plan"]))
    return {"output": res}

def code_evaluator_node(state: AgentState):
    agent = CodeEvaluatorAgent()
    res = asyncio.run(agent.evaluate_code(state["input"], state["output"]))
    return {"evaluation_feedback": res}

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
    workflow.add_edge("evaluator", END)
    
    return workflow.compile()
