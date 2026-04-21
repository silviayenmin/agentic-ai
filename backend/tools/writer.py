import os
from pydantic import BaseModel, Field
from langchain_core.tools import tool


# Input schema
class WriteFileInput(BaseModel):
    file_name: str = Field(..., description="File name inside workspace (e.g., demo.txt)")
    content: str = Field(..., description="Content to write into the file")
    mode: str = Field("w", description="Write mode: always overwrite")


# Base directory → workspace
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "workspace")
)


@tool(args_schema=WriteFileInput)
def write_file_tool(file_name: str, content: str, mode: str = "w") -> str:
    """
    Writes content to a file inside the workspace directory.
    Default mode is overwrite.
    """
    try:
        full_path = os.path.join(BASE_DIR, file_name)

        print(f"Checking path: {full_path}")

        if not os.path.isfile(full_path):
            return "File not found in workspace."

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
    result = write_file_tool.invoke({
        "file_name": file_name,
        "content": content
    })

    print("\nResult:")
    print(result)
    
