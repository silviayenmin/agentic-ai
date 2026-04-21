import os
import json
import asyncio
import sys
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
 
 
class ReaderInput(BaseModel):
    """Input schema for reading a file."""
 
    file_path: str = Field(
        ...,
        description="The absolute path to the file that needs to be read.",
    )
 
async def read_file_content(file_path: str) -> Dict[str, Any]:
    """
    Reads the content of a file and returns it in a structured dictionary.
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
 
        # For large files, you might want to stream or read in chunks,
        # but for a tool, we typically read the whole content if it's manageable.
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
 
        return {
            "status": "success",
            "file_path": file_path,
            "content": content,
        }
 
    except Exception as e:
        return {
            "status": "error",
            "file_path": file_path,
            "error_message": str(e),
        }
 
 
@tool(args_schema=ReaderInput)
async def read_file(file_path: str) -> str:
    """
    Reads a file from the local filesystem and returns its content.
    Useful for agents to understand file contents or configurations.
    """
    result = await read_file_content(file_path)
    # return json.dumps(result, indent=2)
    return result
 
 
if __name__ == "__main__":
    # Local test
    async def test():
        # Check if a path was provided in the command line, otherwise use this file
        if len(sys.argv) > 1:
            test_file = os.path.abspath(sys.argv[1])
        else:
            test_file = os.path.abspath(__file__)
            
        print(f"Testing read_file tool on: {test_file}")
       
        res = await read_file.ainvoke({
            "file_path": test_file
        })
       
        print("\nTool Output:")
        print(res)
 
    asyncio.run(test())
 
 
