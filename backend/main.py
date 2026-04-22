import os
import json
import re
import asyncio
from typing import Annotated, TypedDict, List, Union, Literal, Dict, Optional
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from langchain.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

load_dotenv()

app = FastAPI(title="Agentic AI: Professional Dashboard API")

# --- MongoDB Setup ---
# MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
MONGO_URI = os.getenv("MONGO_URI")
LLM_URL = os.getenv("LLM_URL")
# Use a short timeout so the app doesn't hang if MongoDB is offline
client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=2000)
db = client["agentic_ai"]
projects_col = db["projects"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            try:
                self.active_connections.remove(websocket)
            except:
                pass

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except (WebSocketDisconnect, Exception):
                self.disconnect(connection)


manager = ConnectionManager()


# --- Agent State ---
# --- Structured Schemas ---
class Sprint(BaseModel):
    id: int
    title: str
    goal: str
    features: List[str]


class SprintsOutput(BaseModel):
    sprints: List[Sprint]


class Task(BaseModel):
    id: int
    title: str
    description: str
    assigned_to: str
    priority: Literal["High", "Medium", "Low"]


class TasksOutput(BaseModel):
    backlog: List[Task]


class CodeFilesOutput(BaseModel):
    filenames: List[str]


class FileAssignment(BaseModel):
    filename: str
    task_ids: List[int]
    description: str


class ProjectPlan(BaseModel):
    assignments: List[FileAssignment]
    architecture_notes: str


class QAReport(BaseModel):
    status: Literal["PASSED", "FAILED"]
    bugs: List[str]
    suggestions: List[str]


# --- Agent State ---
class AgentState(TypedDict):
    project_id: str
    user_id: str
    project_requirements: str
    provider: str
    model: str
    sprints: List[dict]
    tasks: List[dict]
    codebase: dict
    qa_report: dict
    current_agent: str
    agent_statuses: Dict[str, str]
    logs: List[str]
    iteration_count: int


# --- Persistence Helpers ---
async def persist_state(state: AgentState):
    """Saves the current state to MongoDB (Safely)."""
    project_id = state.get("project_id")
    if not project_id:
        return

    doc = {
        "project_id": project_id,
        "user_id": state.get("user_id", "anonymous"),
        "requirements": state.get("project_requirements", ""),
        "state": dict(state),
        "updated_at": datetime.utcnow(),
    }

    try:
        await projects_col.update_one(
            {"project_id": project_id}, {"$set": doc}, upsert=True
        )
        print(f"[Storage] State persisted for project {project_id}")
    except Exception as e:
        print(f"[Storage Warning] Could not persist to DB: {e}")


# --- Helpers ---
def get_llm(provider: str, model_id: str):
    # if provider == "openai":
    #     return ChatOpenAI(model=model_id, temperature=0)
    # elif provider == "anthropic":
    #     return ChatAnthropic(model=model_id, temperature=0)
    # else:
    # For Ollama, we ensure format="json" if using with_structured_output later
    return Ollama(model=model_id, temperature=0, base_url=LLM_URL)
    # return Ollama(model=model_id, temperature=0, base_url="http://localhost:11434")


async def notify(agent: str, message: str, state: AgentState):
    log_entry = f"[{agent}] {message}"
    state["logs"].append(log_entry)
    print(log_entry)  # Always log to terminal

    # CRITICAL: We broadcast in a try/except block so a disconnect NEVER crashes the agent
    try:
        payload = {
            "type": "update",
            "agent": agent,
            "message": message,
            "state": {
                "sprints": state.get("sprints", []),
                "tasks": state.get("tasks", []),
                "codebase": state.get("codebase", {}),  # Send full codebase
                "qa_report": state.get("qa_report", {}),
                "agent_statuses": state.get("agent_statuses", {}),
                "current_agent": state.get("current_agent", ""),
            },
        }
        await manager.broadcast(payload)
    except Exception as e:
        print(f"Broadcast failed (likely disconnect): {e}")


# --- Nodes ---
async def business_analyst(state: AgentState):
    state["current_agent"] = "BA"
    state["agent_statuses"]["BA"] = "working"
    await notify("BA", "Analyzing requirements and designing sprints...", state)

    llm = get_llm(state["provider"], state["model"]).with_structured_output(
        SprintsOutput
    )
    prompt = f"You are an expert Business Analyst. Create a technical spec and list of sprints for this project: {state['project_requirements']}."

    try:
        result = llm.invoke(prompt)
        state["sprints"] = [s.dict() for s in result.sprints]
        state["agent_statuses"]["BA"] = "done"
        await notify(
            "BA", f"Plan finalized with {len(state['sprints'])} sprints.", state
        )
    except Exception as e:
        await notify("BA", f"Error in analysis: {e}", state)
        state["agent_statuses"]["BA"] = "failed"

    await persist_state(state)
    return state


async def project_manager(state: AgentState):
    state["current_agent"] = "PM"
    state["agent_statuses"]["PM"] = "working"
    await notify("PM", "Generating task backlog...", state)

    llm = get_llm(state["provider"], state["model"]).with_structured_output(TasksOutput)
    prompt = f"You are an expert Project Manager. Review these sprints: {json.dumps(state['sprints'])}. Generate a detailed task backlog for the Developer."

    try:
        result = llm.invoke(prompt)
        state["tasks"] = [t.dict() for t in result.backlog]
        state["agent_statuses"]["PM"] = "done"
        await notify(
            "PM",
            f"Project APPROVED. Assigned {len(state['tasks'])} tasks to Developers.",
            state,
        )
    except Exception as e:
        await notify("PM", f"Error creating backlog: {e}", state)
        state["agent_statuses"]["PM"] = "failed"

    await persist_state(state)
    return state


async def developer(state: AgentState):
    state["current_agent"] = "Dev"
    state["agent_statuses"]["Dev"] = "working"
    state["iteration_count"] += 1

    if state["iteration_count"] > 1:
        await notify(
            "Dev",
            f"Strictly fixing bugs (Iteration {state['iteration_count']})...",
            state,
        )
    else:
        await notify(
            "Dev",
            "Software Architect initialized. Partitioning tasks to files...",
            state,
        )

    llm = get_llm(state["provider"], state["model"])

    # 1. Architectural Mapping: Assign specific tasks to specific files
    architect = llm.with_structured_output(ProjectPlan)
    arch_prompt = f"""
    You are a Senior Software Architect. 
    Tasks: {json.dumps(state['tasks'])}
    Requirements: {state['project_requirements']}
    
    GOAL: Design a clean, modular FastAPI project structure. 
    1. Determine the filenames needed (e.g., main.py, app/routes/greet.py).
    2. Assign each individual Task (by ID) to exactly ONE file to prevent duplication.
    3. Ensure 'main.py' is the entry point that initializes the app and includes routers.
    """

    try:
        plan = architect.invoke(arch_prompt)
        assignments = plan.assignments
    except Exception as e:
        await notify(
            "Dev",
            f"Architectural Mapping failed: {e}. Falling back to single file.",
            state,
        )
        assignments = [
            FileAssignment(
                filename="main.py",
                task_ids=[t["id"] for t in state["tasks"]],
                description="Full implementation",
            )
        ]

    # 2. Targeted Generation: Write each file with ISOLATED context
    for assignment in assignments:
        fname = assignment.filename
        assigned_tasks = [t for t in state["tasks"] if t["id"] in assignment.task_ids]

        if not assigned_tasks and fname != "main.py":
            continue

        await notify(
            "Dev", f"Developing {fname} (Tasks: {assignment.task_ids})...", state
        )

        qa_feedback = ""
        if state["iteration_count"] > 1 and state["qa_report"].get("bugs"):
            qa_feedback = f"QA COMPLIANCE: {json.dumps(state['qa_report']['bugs'])}. FIX ONLY THE BUGS IN {fname}."

        file_prompt = f"""
        Role: Senior Developer
        File: {fname}
        Module Goal: {assignment.description}
        Specific Tasks to Implement: {json.dumps(assigned_tasks)}
        
        PROJECT CONTEXT (READ ONLY):
        Global Requirements: {state['project_requirements']}
        Architecture Plan: {plan.architecture_notes if 'plan' in locals() else ""}
        Current Codebase (for imports/signatures): {json.dumps({k: v[:500] for k, v in state['codebase'].items()})}
        {qa_feedback}
        
        STRICT CODING STANDARDS:
        1. ONLY implement the 'Specific Tasks' assigned to this file. 
        2. DO NOT implement logic found in other tasks/files to avoid duplication.
        3. Use 'APIRouter' for routes in sub-files. DO NOT create new FastAPI() instances.
        4. If this is 'main.py', include the routers from other files.
        5. Return ONLY raw source code. No introductory text. No markdown.
        """

        res = llm.invoke(file_prompt)
        content = res.content

        # Robust Markdown Extraction
        if "```" in content:
            match = re.search(r"```(?:\w+)?\n?(.*?)\n?```", content, re.DOTALL)
            content = match.group(1) if match else content.replace("```", "")

        state["codebase"][fname] = str(content).strip()

    state["agent_statuses"]["Dev"] = "done"
    await notify(
        "Dev",
        f"Modular development phase complete ({len(assignments)} modules).",
        state,
    )
    await persist_state(state)
    return state


async def testing_agent(state: AgentState):
    state["current_agent"] = "QA"
    state["agent_statuses"]["QA"] = "working"
    await notify("QA", "Performing Audit for Modularity and Standards...", state)

    llm = get_llm(state["provider"], state["model"]).with_structured_output(QAReport)
    prompt = f"""
    You are a Strict Code Auditor. 
    Codebase: {json.dumps(state['codebase'])}
    
    CRITICAL AUDIT RULES:
    1. DUPLICATION: Does the same path (e.g. /greet) exist in multiple files? If so, FAIL.
    2. MODULARITY: Are sub-files using APIRouter? Does 'main.py' correctly include them?
    3. STANDARDS: Is there any introductory text or markdown backticks in the code?
    4. LOGIC: Does the code fulfill these requirements: {state['project_requirements']}?

    Return a structured report.
    """

    try:
        result = llm.invoke(prompt)
        state["qa_report"] = result.dict()
        state["agent_statuses"]["QA"] = "done"
        await notify(
            "QA", f"Audit Finished. Result: {state['qa_report']['status']}", state
        )
    except Exception as e:
        await notify("QA", f"Audit Error: {e}", state)
        state["qa_report"] = {"status": "FAILED", "bugs": [str(e)], "suggestions": []}

    await persist_state(state)
    return state


async def monitor_agent(state: AgentState):
    state["current_agent"] = "Monitor"
    state["agent_statuses"]["Monitor"] = "working"
    await notify("Monitor", "Delivering to workspace...", state)

    # Ensure we always write to the root workspace, not backend/workspace
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workspace_dir = os.path.join(root_dir, "workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    for fname, content in state["codebase"].items():
        try:
            # Ensure the content is a string before writing
            if isinstance(content, str):
                file_path = os.path.join(workspace_dir, fname)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                await notify(
                    "Monitor",
                    f"Warning: Content for {fname} was not a string, skipping file write.",
                    state,
                )
        except Exception as e:
            await notify("Monitor", f"Error writing file {fname}: {e}", state)

    state["agent_statuses"]["Monitor"] = "done"
    await notify("Monitor", "Project delivered successfully.", state)
    await persist_state(state)
    return state


def should_continue(state: AgentState):
    if state["qa_report"].get("status") == "PASSED" or state["iteration_count"] >= 10:
        return "Monitor"
    return "Dev"


# --- Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("BA", business_analyst)
workflow.add_node("PM", project_manager)
workflow.add_node("Dev", developer)
workflow.add_node("QA", testing_agent)
workflow.add_node("Monitor", monitor_agent)

workflow.set_entry_point("BA")
workflow.add_edge("BA", "PM")
workflow.add_edge("PM", "Dev")
workflow.add_edge("Dev", "QA")
workflow.add_conditional_edges(
    "QA", should_continue, {"Dev": "Dev", "Monitor": "Monitor"}
)  # Explicitly map
workflow.add_edge("Monitor", END)
agent_graph = workflow.compile()


# --- API ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            req = json.loads(data)
            if req["type"] == "start":
                project_id = str(uuid.uuid4())
                user_id = req.get("user_id", "anonymous")
                initial_state = {
                    "project_id": project_id,
                    "user_id": user_id,
                    "project_requirements": req["requirements"],
                    "provider": "ollama",
                    "model": "qwen2.5-coder:14b",
                    "sprints": [],
                    "tasks": [],
                    "codebase": {},
                    "qa_report": {},
                    "current_agent": "BA",
                    "agent_statuses": {
                        "BA": "idle",
                        "PM": "idle",
                        "Dev": "idle",
                        "QA": "idle",
                        "Monitor": "idle",
                    },
                    "logs": [],
                    "iteration_count": 0,
                }
                # Initial persistence
                await persist_state(initial_state)
                asyncio.create_task(agent_graph.ainvoke(initial_state))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# --- Project Management Endpoints ---
@app.get("/projects")
async def list_projects(user_id: str):
    """Lists all projects for a specific user (Safely)."""
    try:
        # Sort by updated_at descending
        projects = (
            await projects_col.find({"user_id": user_id})
            .sort("updated_at", -1)
            .to_list(length=100)
        )
        # Convert BSON/ObjectId to strings for JSON serialization
        for p in projects:
            p["_id"] = str(p["_id"])
            if "updated_at" in p:
                p["updated_at"] = p["updated_at"].isoformat()
        return projects
    except Exception as e:
        print(f"[Storage Warning] Could not fetch projects: {e}")
        return []


@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Retrieves a specific project's full state (Safely)."""
    try:
        project = await projects_col.find_one({"project_id": project_id})
        if project:
            project["_id"] = str(project["_id"])
            if "updated_at" in project:
                project["updated_at"] = project["updated_at"].isoformat()
            return project
        raise HTTPException(status_code=404, detail="Project not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Storage Warning] Could not fetch project detail: {e}")
        return {"error": "Database offline"}


@app.get("/")
def read_root():
    return {"status": "online"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
