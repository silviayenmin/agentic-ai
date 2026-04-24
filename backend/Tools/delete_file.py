import os
from langchain_core.tools import tool
from config_loader import get_workspace_dir

@tool
def delete_file_tool(file_path: str) -> str:
    """
    Deletes a file from the workspace. 
    USE WITH CAUTION.
    
    Args:
        file_path: The relative path to the file to delete.
    """
    workspace = get_workspace_dir()
    full_path = os.path.abspath(os.path.join(workspace, file_path))
    
    # Security: Ensure the path is within the workspace
    if not full_path.startswith(os.path.abspath(workspace)):
        return f"Error: Access denied to path outside workspace: {file_path}"
    
    if not os.path.exists(full_path):
        return f"Error: File not found: {file_path}"
    
    if os.path.isdir(full_path):
        return f"Error: Cannot delete a directory using this tool: {file_path}"
    
    try:
        os.remove(full_path)
        return f"Successfully deleted file: {file_path}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"
