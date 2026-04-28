import os
import shutil
from langchain_core.tools import tool
from config_loader import get_workspace_dir

@tool
def delete_directory_tool(directory_path: str) -> str:
    """
    Deletes a directory and all its contents (files and subdirectories) recursively.
    USE WITH EXTREME CAUTION.
    
    Args:
        directory_path: The relative path to the directory to delete.
    """
    workspace = get_workspace_dir()
    full_path = os.path.abspath(os.path.join(workspace, directory_path))
    
    # Security: Ensure the path is within the workspace
    if not full_path.startswith(os.path.abspath(workspace)):
        return f"Error: Access denied to path outside workspace: {directory_path}"
    
    if not os.path.exists(full_path):
        return f"Error: Directory not found: {directory_path}"
    
    if not os.path.isdir(full_path):
        return f"Error: Path is not a directory: {directory_path}. Use delete_file_tool instead."
    
    try:
        shutil.rmtree(full_path)
        return f"Successfully deleted directory and all contents: {directory_path}"
    except Exception as e:
        return f"Error deleting directory: {str(e)}"
