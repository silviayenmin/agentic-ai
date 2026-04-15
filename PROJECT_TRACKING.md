# Agentic AI Multi-Agent System: Project Tracking

## 🚀 Project Overview
An autonomous multi-agent system designed to take high-level requirements and deliver a fully functional software project through a collaborative pipeline of specialized AI agents.

## 🛠️ Technology Stack & Dependencies

| Package | Purpose | Reason |
| :--- | :--- | :--- |
| **FastAPI** | Backend Framework | High performance, native async support, and excellent for building REST/WebSocket APIs. |
| **LangGraph** | Agent Orchestration | Provides fine-grained control over agent cycles and state management, essential for "QA -> Dev" feedback loops. |
| **LangChain** | LLM Framework | Industry standard for tool-calling and standardizing interfaces across different LLM providers. |
| **React + Vite** | Frontend | Fast development cycle and modern UI capabilities for the Agent Dashboard. |
| **Tailwind CSS** | Styling | Rapid UI development with a clean, modern aesthetic. |
| **WebSockets** | Real-time Comms | Allows the UI to stream agent logs and status updates instantly. |
| **Ollama** | Local LLM Support | Enables privacy-focused or cost-effective local execution of models like Llama 3 or Mistral. |

## 🤖 Agent Roles & Models

| Agent | Role | Recommended Model |
| :--- | :--- | :--- |
| **Business Analyst (BA)** | Requirement decomposition & Sprint planning | GPT-4o / Claude 3.5 Sonnet (High reasoning) |
| **Project Manager (PM)** | Task assignment & Review | GPT-4o / Claude 3.5 Sonnet (Coordination) |
| **Developer (Dev)** | Code generation & Bug fixing | Claude 3.5 Sonnet / Llama 3 (Strong coding logic) |
| **Testing (QA)** | Test case generation & Validation | GPT-4o (Precise scenario analysis) |
| **Monitor** | Progress tracking & Delivery | GPT-4o mini / Llama 3 (State monitoring) |

## 🗺️ Implementation Roadmap

### Phase 1: Foundation (COMPLETED)
- [x] Create project structure (`backend`, `frontend`, `workspace`).
- [x] Initialize `backend` with FastAPI and Structured LangGraph state.
- [x] Implement Model Factory (OpenAI, Claude, Ollama support).
- [x] Setup `frontend` with Vite + React + TypeScript and modern layout.

### Phase 2: Agent Logic (COMPLETED)
- [x] Define BA & PM Pydantic schemas and output parsing.
- [x] Implement Dev agent with enhanced file_system delivery.
- [x] Implement QA agent with structured auditing capabilities.

### Phase 3: Orchestration & UI
- [ ] Connect agents via LangGraph cycles.
- [ ] Build the WebSocket log streamer.
- [ ] Create the Dashboard UI (Kanban board + Agent logs).

### Phase 4: Delivery & Optimization
- [ ] Implement the "Project Export" feature.
- [ ] Add support for negative scenario testing in QA.
- [ ] Final E2E testing with complex requirements.

## 📝 Instructions for Running
*(Detailed instructions will be added as components are implemented)*
1. **Backend:** `pip install -r requirements.txt` -> `uvicorn main:app --reload`
2. **Frontend:** `npm install` -> `npm run dev`
