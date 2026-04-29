# Agent Knowledge Base

This file contains persistent context and long-term goals for the multi-agent system. Unlike `analysis.md` or `plan.md`, this file is intended to be a stable "Source of Truth" to prevent agent confusion.

## Project Vision
- A robust, multi-agent orchestration framework for autonomous software development.
- Focus on modularity, observability, and iterative refinement.

## Core Principles
1. **Verification First**: Every file operation must be verified for success.
2. **Context Awareness**: Use the `agent_knowledge.md` and `tasks.md` to maintain state.
3. **Tool Precision**: Use the most specific tool for each task. Pass ONLY the required arguments defined in the tool schema.
4. **Task Decomposition**: Split continuous or complex tasks into atomic, verifiable steps. Complete one step perfectly before moving to the next.
5. **Non-Blocking Operations**: When starting servers or background tasks, use `is_background: true`. Accept "Background process started" as a successful confirmation and continue with other tasks.
6. **Verification Obligation**: For major project milestones (e.g., project initialization, multi-file generation), you MUST use the `verify_integrity` tool to confirm that all expected files exist and are correctly populated. Do not move to the next task until integrity is confirmed.
7. **Efficiency Flags**: When initializing new projects (e.g., NestJS, React, Next.js), ALWAYS use flags to skip immediate dependency installation (e.g., `--skip-install`, `--no-install`). This allows for rapid scaffolding. Dependencies should be installed as a separate, background step if needed.
8. **Direct Pathing (ONLY '{workspace_name}/')**: Your ONLY workspace is the '{workspace_name}/' directory. All project scaffolding, file creation, and command execution MUST happen inside '{workspace_name}/'. If the folder is missing, create it. If you are asked to create a project named `candle`, the files should be in '{workspace_name}/candle/'. NEVER create projects in the root directory.

## Current High-Level Objectives
- Enhance agent stability and reasoning capabilities.
- Implement strict verification loops for all destructive or creative actions.
- Improve project structure exploration with recursive tools.
