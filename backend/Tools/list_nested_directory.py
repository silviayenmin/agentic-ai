import os
from typing import List, Dict, Union
from langchain_core.tools import tool
import sys

# Add parent directory to path to import config_loader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import get_workspace_dir

@tool
def list_nested_directory(path: str = ".", include_all: bool = False) -> str:
    """
    Lists the contents of a directory and all its subdirectories recursively. 
    By default, it ignores heavy directories like node_modules, venv, and .git.
    
    Args:
        path: The relative path to the directory (relative to the workspace root).
        include_all: If True, includes common ignored directories like node_modules and venv.
    """
    workspace = get_workspace_dir()
    full_path = os.path.abspath(os.path.join(workspace, path))
    
    # Common directories to ignore for performance and clarity
    DEFAULT_IGNORE = {
        "node_modules", "venv", ".git", "__pycache__", 
        ".next", ".agent_context", "dist", "build", ".venv"
    }
    
    # Security: Ensure the path is within the workspace
    if not full_path.startswith(os.path.abspath(workspace)):
        return f"Error: Access denied to path outside workspace: {path}"
    
    if not os.path.exists(full_path):
        return f"Error: Path does not exist: {path}"
    
    if not os.path.isdir(full_path):
        return f"Error: Path is not a directory: {path}"
    
    try:
        output = []
        for root, dirs, files in os.walk(full_path):
            # Prune ignored directories in-place to avoid walking into them
            if not include_all:
                dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE and not d.startswith(".")]
            
            # Calculate relative depth for indentation
            rel_root = os.path.relpath(root, full_path)
            if rel_root == ".":
                level = 0
            else:
                level = rel_root.count(os.sep) + 1
            
            indent = "  " * level
            if rel_root != ".":
                output.append(f"{indent}[DIR] {os.path.basename(root)}")
            else:
                output.append(f"[WORKSPACE]")
            
            sub_indent = "  " * (level + 1)
            for f in sorted(files):
                if not include_all and f.startswith("."):
                    continue
                output.append(f"{sub_indent}[FILE] {f}")
                
        if not output:
            return f"Directory '{path}' is empty."
            
        return "\n".join(output)
    except Exception as e:
        return f"Error listing nested directory: {str(e)}"
