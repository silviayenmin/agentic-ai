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
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(backend_dir, workspace_name)

def get_workspace_name():
    config = load_global_config()
    return config.get("workspace_dir", "workspace")
