import os
import sys
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Add parent directory to path to import config_loader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import get_workspace_dir

class CreateDirectoryInput(BaseModel):
    path: str = Field(..., description="The relative path of the directory to create.")

@tool(args_schema=CreateDirectoryInput)
def create_directory(path: str) -> str:
    """
    Creates a directory and any missing parent directories.
    Ensures the directory is created within the workspace.
    """
    try:
        workspace = get_workspace_dir()
        # Normalize and join with workspace
        full_path = os.path.normpath(os.path.join(workspace, path))
        
        # Security check: Ensure it's inside the workspace
        if not full_path.startswith(os.path.abspath(workspace)):
            return f"Error: Path '{path}' is outside the allowed workspace."

        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                return f"Directory already exists: {path}"
            else:
                return f"Error: A file already exists at this path: {path}"

        os.makedirs(full_path, exist_ok=True)
        return f"Successfully created directory: {path}"
        
    except Exception as e:
        return f"Error creating directory: {str(e)}"
