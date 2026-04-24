import os
from typing import List, Dict, Union
from langchain_core.tools import tool
from config_loader import get_workspace_dir

@tool
def list_directory_tool(path: str = ".") -> str:
    """
    Lists the contents of a directory. 
    Use this to explore the project structure.
    
    Args:
        path: The relative path to the directory (relative to the workspace root).
    """
    workspace = get_workspace_dir()
    full_path = os.path.abspath(os.path.join(workspace, path))
    
    # Security: Ensure the path is within the workspace
    if not full_path.startswith(os.path.abspath(workspace)):
        return f"Error: Access denied to path outside workspace: {path}"
    
    if not os.path.exists(full_path):
        return f"Error: Path does not exist: {path}"
    
    if not os.path.isdir(full_path):
        return f"Error: Path is not a directory: {path}"
    
    try:
        items = os.listdir(full_path)
        if not items:
            return f"Directory '{path}' is empty."
            
        details = []
        for item in items:
            item_path = os.path.join(full_path, item)
            is_dir = os.path.isdir(item_path)
            prefix = "[DIR] " if is_dir else "[FILE]"
            details.append(f"{prefix} {item}")
            
        return "\n".join(sorted(details))
    except Exception as e:
        return f"Error listing directory: {str(e)}"
