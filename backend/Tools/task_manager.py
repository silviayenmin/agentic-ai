import os
import re
from typing import List, Dict, Optional
from langchain_core.tools import tool
from config_loader import get_workspace_dir

TASK_FILE = ".agent_context/tasks.md"

@tool
def update_task_status(task_name: str, status: str, notes: Optional[str] = None) -> str:
    """
    Updates the status of a specific task in the project task list.
    Status can be: TODO, IN_PROGRESS, DONE, FAILED.
    
    Args:
        task_name: The name or brief description of the task to update.
        status: The new status (TODO, IN_PROGRESS, DONE, FAILED).
        notes: Optional feedback or technical notes about the task completion.
    """
    workspace = get_workspace_dir()
    full_path = os.path.join(workspace, TASK_FILE)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    content = ""
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
    
    status_icon = {
        "TODO": "[ ]",
        "IN_PROGRESS": "[/]",
        "DONE": "[x]",
        "FAILED": "[!]"
    }.get(status.upper(), "[ ]")
    
    # Simple search and replace if task exists, otherwise append
    lines = content.splitlines()
    found = False
    new_lines = []
    
    task_pattern = re.compile(rf"\[.\]\s*{re.escape(task_name)}", re.IGNORECASE)
    
    for line in lines:
        if task_pattern.search(line):
            new_line = f"{status_icon} {task_name}"
            if notes:
                new_line += f" - {notes}"
            new_lines.append(new_line)
            found = True
        else:
            new_lines.append(line)
            
    if not found:
        new_line = f"{status_icon} {task_name}"
        if notes:
            new_line += f" - {notes}"
        new_lines.append(new_line)
        
    with open(full_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
        
    return f"Task '{task_name}' updated to {status}."

@tool
def get_task_list() -> str:
    """
    Retrieves the current project task list and their statuses.
    """
    workspace = get_workspace_dir()
    full_path = os.path.join(workspace, TASK_FILE)
    
    if not os.path.exists(full_path):
        return "No task list found. You should create one using update_task_status."
        
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()
