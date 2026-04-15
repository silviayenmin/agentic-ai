# Technical Reference: Agentic AI Ecosystem v2.5 (Professional)

This document summarizes the technical architecture, stack, and core code improvements made during the upgrade of the Agentic AI Multi-Agent system. Use this for team training and Knowledge Transfer (KT).

---

## 🏗️ Core Architecture Overview

The system is built as a **Multi-Agent Orchestrator** using a "State-Managed Graph" approach. It decomposes complex software requirements into smaller, verifiable chunks processed by specialized AI agents.

### High-Level Flow (v2.5 Modular Approach)
1. **BA (Architect)**: Requirement → Project Spec & Feature Map.
2. **PM (Planner)**: Features → Granular **Task Backlog** with specific IDs.
3. **Dev (Senior Developer)**: 
    - **Step A (Allocation)**: Maps every backlog task to a specific target file.
    - **Step B (Generation)**: Implements files in isolation to ensure **Zero Duplication**.
4. **QA (Critic)**: Codebase → Strict Audit for Modularity, Duplication, and Logic.
5. **Monitor (Deployer)**: Validated Code → Persistent Local Workspace.

---

## 🛠️ Technology Stack

### Backend (The "Brain")
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Async REST & WebSocket support).
- **Orchestration**: [LangGraph](https://langchain-ai.github.io/langgraph/) (Stateful, multi-agent workflows with cycles).
- **Persistence**: [Motor](https://motor.readthedocs.io/) (Async Driver for **MongoDB**).
- **AI Framework**: [LangChain](https://www.langchain.com/) (Interface for LLM tool-calling and memory).
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/).
- **LLM Support**: 
    - **Cloud**: OpenAI (GPT-4o), Anthropic (Claude 3.5).
    - **Local**: Ollama (Llama 3, Mistral, Gemma).

### Frontend (The "Dashboard")
- **Build Tool**: [Vite](https://vitejs.dev/) (Lightning-fast HMR).
- **Logic**: [React 18](https://react.dev/) with **TypeScript**.
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) (Utility-first CSS).
- **Animations**: [Framer Motion](https://www.framer.com/motion/) (Smooth transitions and agent status pulses).
- **Icons**: [Lucide React](https://lucide.dev/).

---

## 🚀 Key Technical Enhancements (v2.0)

### 1. Robust Data Handling (Structured Output)
In the previous version, agents returned raw text, and we used regex to find JSON. This failed frequently if the LLM added conversational text.
- **Improved**: We now use `.with_structured_output(PydanticModel)`.
- **Benefit**: The LLM is forced by the schema to return valid JSON. If it fails, the system catches the error at the node level before it breaks the graph.

```python
# Example: Pydantic Schema used by the BA Agent
class SprintsOutput(BaseModel):
    sprints: List[Sprint]

# Agent usage
llm = get_llm(provider, model).with_structured_output(SprintsOutput)
result = llm.invoke(prompt) # result is guaranteed to be a SprintsOutput object
```

### 2. Real-Time State Sync (WebSockets)
- **Implementation**: The backend broadcasts a full state update to the `/ws` endpoint every time an agent completes a task or logs a message.
- **Optimization**: The frontend maintains a local "Mirror State," allowing for instant UI updates (like tab switching) without checking API endpoints repeatedly.

### 3. Persistent Project History (MongoDB)
- **Problem**: In-memory state was lost on server restart.
- **v2.5 Solution**: Added a `projects` collection in MongoDB.
- **Logic**:
    - **Auto-Save**: The `persist_state` helper is called at the end of every agent node.
    - **History API**: `/projects?user_id=...` allows the dashboard to reload any past project and its full file tree.

### 4. Zero-Duplication "Partitioned Development"
- **Problem**: Small LLMs (like Llama 3) often duplicate routes across `main.py` and modular files.
- **v2.5 Solution**: A two-stage Developer node.
    - **Architect Step**: Partitions tasks before writing. Each task is mapped to *exactly one* filename.
    - **Isolation Step**: The coder agent only "sees" the tasks for the current file, making duplication impossible.

### 5. Classic Professional Dashboard UI
- **Design System**: Restored the "Classic Wide" layout for high-resolution development monitors.
- **Key Features**:
    - **Sidebar**: Collapsible project history panel.
    - **User Onboarding**: Multi-user isolation using "Professional IDs" stored in `localStorage`.
    - **Responsive Grid**: Full-width monitoring with side-by-side terminal and code viewer.

---

## 🔧 Maintenance & Extension

### Adding a New Agent
1. Define a new node function in `backend/main.py`.
2. Add the agent to the `AgentState` TypedDict.
3. Add a node and edge to the LangGraph `StateGraph`.
4. Update the `AgentGrid` in the React frontend to display the new card.

### Improving the QA Loop
The system currently has a cycle: `QA -> should_continue -> Dev`. 
- **To scale**: You can update the `QA` node to use `subprocess` to actually execute the generated code in a docker container and feed the stdout/stderr back into the `Dev` prompt for real debugging.

---

## 📁 File Structure Reference
```text
├── backend/
│   ├── main.py          # LangGraph logic, FastAPI endpoints
│   ├── requirements.txt # Python dependencies
│   └── workspace/       # Default output folder for agents
├── frontend/
│   ├── src/
│   │   ├── App.tsx      # Main dashboard logic
│   │   └── index.css    # Global styles & Tailwind
│   ├── vite.config.ts   # Proxy settings for API
│   └── package.json     # Node.js dependencies
└── README.md            # Entry point documentation
```

**Technical Documentation authored by Antigravity AI.**
