# Senior Developer (Dev) Agent

## Role
The Senior Developer agent is responsible for translating the project manager's task backlog into functional source code. It iteratively generates and refines code based on requirements and bug reports from the QA agent.

## Responsibilities
-   Generate a list of all required project files.
-   Write the source code for each file, one by one.
-   Integrate different parts of the codebase (e.g., backend, frontend, data storage).
-   Fix bugs identified by the QA agent.

## What it Does
-   Receives `tasks` from the PM agent and `project_requirements`.
-   If `qa_report` indicates `FAILED` status, it receives bug details to fix existing code.
-   Uses an LLM (based on user's `provider` and `model` choice) in two phases:
    1.  **Planning**: Asks the LLM for a JSON list of filenames (`["main.py", "index.html", "data.json"]`) required for the project.
    2.  **Coding**: For each identified filename, it asks the LLM to write the raw source code for that specific file.
-   Stores the generated code in the `codebase` dictionary (filename -> content).
-   Cleans up markdown code blocks if the LLM accidentally includes them.

## Input Data
-   `state["tasks"]` (List[dict]): The prioritized list of tasks from the PM agent.
-   `state["project_requirements"]` (string): (Context for the LLM) The overall project goal.
-   `state["codebase"]` (dict): The current state of the codebase (empty initially, or existing code for bug fixes).
-   `state["qa_report"]` (dict): (Optional) The QA report, including `status` and `bugs` found, if a previous iteration failed.
-   `state["provider"]` (string): The chosen LLM provider.
-   `state["model"]` (string): The specific LLM model ID.

## Output Data (Transfers to QA Agent)
-   `state["codebase"]` (dict): A dictionary mapping filenames to their generated source code content (e.g., `{"main.py": "import fastapi...", "index.html": "<!DOCTYPE html>..."}`).
-   `state["iteration_count"]` (int): Increments to track how many times the Dev agent has run.
-   `state["logs"]` (List[str]): Appends log entries detailing its activity.
-   `state["agent_statuses"]["Dev"]` (string): Updates its status to "working" then "done".
-   `state["current_agent"]` (string): Sets the current active agent to "Dev".
