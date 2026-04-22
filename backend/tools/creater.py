import os
import json
import asyncio
import sys
from typing import Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class CreateFileInput(BaseModel):
    """Input schema for creating a file."""

    file_path: str = Field(
        ...,
        description="The absolute path where the file should be created.",
    )
    content: str = Field(
        default="",
        description="Optional content to write into the file if it is created.",
    )


import sys
# Add parent directory to path to import config_loader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import get_workspace_dir

async def create_file_if_not_exists(file_path: str, content: str = "") -> Dict[str, Any]:
    """
    Creates a new file if it does not already exist.
    Ensures safe execution without overwriting existing files.
    """
    try:
        base_dir = Path(get_workspace_dir()).resolve()
        # path = Path(file_path).resolve()
        path = (base_dir / file_path).resolve()
        
        if not str(path).startswith(str(base_dir)):
            return {
                "status": "error",
                "file_path": file_path,
                "error_message": "Invalid path: outside allowed output directory"
            }

        # Check if path exists
        if path.exists():
            if path.is_file():
                return {
                    "status": "success",
                    "file_path": file_path,
                    "message": "File already exists. No action taken.",
                }
            else:
                return {
                    "status": "error",
                    "file_path": file_path,
                    "error_message": "Path exists but is a directory",
                }

        # Ensure parent directories exist
        path.parent.mkdir(parents=True, exist_ok=True)

        # Create file
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "status": "success",
            "file_path": file_path,
            "message": "File created successfully",
        }

    except PermissionError:
        return {
            "status": "error",
            "file_path": file_path,
            "error_message": "Permission denied",
        }

    except OSError as e:
        return {
            "status": "error",
            "file_path": file_path,
            "error_message": e.strerror,
        }

    except Exception as e:
        return {
            "status": "error",
            "file_path": file_path,
            "error_message": str(e),
        }


@tool(args_schema=CreateFileInput)
async def create_file_tool(file_path: str, content: str = "") -> Dict[str, Any]:
    """
    Creates a file only if it does not already exist.
    Prevents overwriting and ensures safe file creation for agents.
    """
    return await create_file_if_not_exists(file_path, content)


if __name__ == "__main__":
    # Local test
    async def test():
        if len(sys.argv) > 1:
            test_file = os.path.abspath(sys.argv[1])
        else:
            test_file = os.path.abspath("test_output.txt")

        print(f"Testing create_file tool on: {test_file}")

        res = await create_file_tool.ainvoke({
            "file_path": test_file,
            "content": "Hello from tool!"
        })

        print("\nTool Output:")
        print(res)

    asyncio.run(test())