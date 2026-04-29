import os
from pydantic import BaseModel, Field
from langchain_core.tools import tool


# Input schema
class WriteFileInput(BaseModel):
    file_name: str = Field(..., description="File name inside the output directory (e.g., demo.txt)")
    content: str = Field(..., description="Content to write into the file")
    mode: str = Field("w", description="Write mode: always overwrite")


import sys
# Add parent directory to path to import config_loader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import get_workspace_dir

# Base directory → from config
BASE_DIR = get_workspace_dir()


@tool(args_schema=WriteFileInput)
def write_to_file(file_name: str, content: str, mode: str = "w") -> str:
    """
    Writes content to a file inside the configured output directory.
    If the file or directory does not exist, it will be created.
    Default mode is overwrite.
    """
    try:
        from config_loader import sanitize_path
        clean_file_name = sanitize_path(file_name)
        full_path = os.path.join(BASE_DIR, clean_file_name)

        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # always overwrite
        with open(full_path, "w", encoding="utf-8") as file:
            file.write(content + "\n")

        return f"Successfully written to '{file_name}'"

    except Exception as e:
        return f"Error: {str(e)}"


# CLI + Tool support
if __name__ == "__main__":
    print("Writer Tool (CLI Mode)")

    file_name = input("Enter file name: ").strip()

    print("Enter content (type 'END' to finish):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)

    content = "\n".join(lines)

    # no mode input — always overwrite
    result = write_to_file.invoke({
        "file_name": file_name,
        "content": content
    })

    print("\nResult:")
    print(result)
    
