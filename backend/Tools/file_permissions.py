import os
import json
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class FilePermissionInput(BaseModel):
    """Input schema for checking file permissions."""
    file_path: str = Field(
        ..., 
        description="The absolute or relative path to the file or directory to check permissions for."
    )

def get_permissions_report(path: str) -> Dict[str, Any]:
    """
    Core logic for checking permissions, decoupled from the LangChain tool decorator.
    Can be reused anywhere in the backend.
    """
    abs_path = os.path.abspath(path)
    parent_dir = os.path.dirname(abs_path)
    exists = os.path.exists(abs_path)
    
    report = {
        "path": abs_path,
        "exists": exists,
        "is_file": os.path.isfile(abs_path),
        "is_dir": os.path.isdir(abs_path),
        "permissions": {
            "read": False,
            "write": False,
            "delete": False,
            "execute": False
        },
        "parent_directory": {
            "path": parent_dir,
            "exists": os.path.exists(parent_dir),
            "writable": False
        },
        "error": None
    }
    
    try:
        # Check current path permissions
        if exists:
            report["permissions"]["read"] = os.access(abs_path, os.R_OK)
            report["permissions"]["write"] = os.access(abs_path, os.W_OK)
            report["permissions"]["execute"] = os.access(abs_path, os.X_OK)
            
        # Check parent directory for 'delete' or 'create' capabilities
        if os.path.exists(parent_dir):
            parent_writable = os.access(parent_dir, os.W_OK)
            report["parent_directory"]["writable"] = parent_writable
            # Deletion requires write permission on the parent directory
            report["permissions"]["delete"] = parent_writable if exists else False
        else:
            if not exists:
                report["error"] = f"Parent directory '{parent_dir}' does not exist."

    except Exception as e:
        report["error"] = str(e)
        
    return report

@tool(args_schema=FilePermissionInput)
def check_file_permissions(file_path: str) -> str:
    """
    Checks the read, write, and delete permissions for a given file path.
    Useful for ensuring the agent has necessary access before performing file operations.
    """
    report = get_permissions_report(file_path)
    return json.dumps(report, indent=2)

