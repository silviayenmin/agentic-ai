# Business Analyst (BA) Agent

## Role
The Business Analyst agent is the initial point of contact for a new project. Its primary function is to interpret high-level user requirements and translate them into actionable technical specifications and structured sprints.

## Responsibilities
-   Understand and decompose vague or high-level project requirements.
-   Define the scope and objectives of the project in technical terms.
-   Break down the project into logical, manageable sprints with clear goals and features.

## What it Does
-   Receives the raw `project_requirements` from the user.
-   Uses an LLM (based on user's `provider` and `model` choice) with a specialized prompt to generate the technical breakdown.
-   Structures its output as a JSON object containing `detailed_spec` and `sprints`.

## Input Data
-   `state["project_requirements"]` (string): The high-level description of the project provided by the user.
-   `state["provider"]` (string): The chosen LLM provider (e.g., "ollama", "openai").
-   `state["model"]` (string): The specific LLM model ID (e.g., "qwen2.5-coder:14b","gpt-4o").

## Output Data (Transfers to PM Agent)
-   `state["sprints"]` (List[dict]): A list of dictionaries, where each dictionary represents a sprint with `id`, `title`, `goal`, and `features`.
-   `state["logs"]` (List[str]): Appends log entries detailing its activity.
-   `state["agent_statuses"]["BA"]` (string): Updates its status to "working" then "done".
-   `state["current_agent"]` (string): Sets the current active agent to "BA".
