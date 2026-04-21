import os
import json
from langchain_core.tools import tool


@tool
def read_file_tool(file_path: str) -> dict:
    """
    Reads a file from the given path and returns structured content.
    """
    try:
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "file_path": file_path,
                "error_message": "File does not exist",
            }

        if not os.path.isfile(file_path):
            return {
                "status": "error",
                "file_path": file_path,
                "error_message": "Path is not a file",
            }

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {"status": "success", "file_path": file_path, "content": content}

    except Exception as e:
        return {"status": "error", "file_path": file_path, "error_message": str(e)}


# if __name__ == "__main__":
#     import sys

#     # Check if a file path was provided as an argument
#     if len(sys.argv) > 1:
#         target_file = sys.argv[1]
#     else:
#         # Default fallback to testing sample.py
#         workspace_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "workspace")
#         target_file = os.path.join(workspace_dir, "backend", "sample.py")
#         print("No file path provided. Falling back to default test file.")

#     print(f"Testing read_file_tool on: {target_file}")

#     # Invoke the tool
#     result = read_file_tool.invoke({"file_path": target_file})

#     print("\nResult:")
#     print(json.dumps(result, indent=2))
