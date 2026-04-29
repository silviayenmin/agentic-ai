import os
import json

def load_global_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}

def get_workspace_dir():
    config = load_global_config()
    workspace_name = config.get("workspace_dir", "workspace")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root_dir, workspace_name)

def get_workspace_name():
    config = load_global_config()
    return config.get("workspace_dir", "workspace")

def sanitize_path(path: str) -> str:
    """
    Recursively strips the workspace directory name from the start of a path.
    Handles 'output/output/src/App.js' -> 'src/App.js'
    """
    if not path:
        return path
    
    workspace_name = get_workspace_name()
    # Normalize separators
    clean_path = path.replace("\\", "/").strip("/")
    
    # Loop to strip multiple layers if the agent is very confused
    while True:
        if clean_path.startswith(f"{workspace_name}/"):
            clean_path = clean_path[len(workspace_name)+1:].strip("/")
        elif clean_path == workspace_name:
            clean_path = "."
            break
        else:
            break
            
    return clean_path
