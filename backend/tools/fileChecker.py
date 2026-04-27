import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class FileCheckerInput(BaseModel):
    """Input schema for checking file existence."""
    target: str = Field(..., description="The name or path of the file to check.")
    search_folder: str = Field("workspace", description="The folder to search in.")

def find_project_root():
    """
    Finds the project root by looking for markers like '.git' or 'backend'.
    """
    current_dir = os.path.abspath(os.getcwd())
    while True:
        if os.path.isdir(os.path.join(current_dir, '.git')) or \
           os.path.isdir(os.path.join(current_dir, 'backend')):
            return current_dir
        
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    return os.path.abspath(os.getcwd())

def _check_file_logic(target: str, search_folder: str = 'workspace') -> str:
    """
    Internal logic for checking if a file exists.
    """
    # Normalize path separators
    target = target.replace('\\', '/')
    
    # Check if it's a direct path starting from current directory
    if os.path.isfile(target):
        return f"SUCCESS: File found at direct path: {target}"
    
    # Check if target is just a filename or a partial path
    target_basename = os.path.basename(target)
    
    root_path = find_project_root()
    target_dir_path = os.path.join(root_path, search_folder)
    
    # Ensure we search exclusively in the specified folder if it exists
    search_dir = target_dir_path if os.path.isdir(target_dir_path) else root_path
    
    # Recursive search from the targeted directory
    for root, dirs, files in os.walk(search_dir):
        for file in files:
            # If we match the filename (case-insensitive)
            if file.lower() == target_basename.lower():
                # Construct the full relative path found
                current_full_path = os.path.join(root, file).replace('\\', '/')
                # Check if it matches the target path provided (case-insensitive)
                if current_full_path.lower().endswith(target.lower()):
                    return f"SUCCESS: File '{target}' found at '{current_full_path}'"
                
    return f"ERROR: File '{target}' not found in '{search_folder}'"

@tool
def check_file_exists(target: str, search_folder: str = 'workspace') -> str:
    """
    Checks if a file exists in a specific folder.
    Returns a descriptive string with the file path if found.
    """
    return _check_file_logic(target, search_folder)

@tool(args_schema=FileCheckerInput)
async def check_file(target: str, search_folder: str = "workspace") -> str:
    """
    Checks if a file exists in a specific folder.
    Supports both direct paths and recursive searching for filenames.
    """
    # Check if file exists using the helper function
    result_str = _check_file_logic(target, search_folder)
    exists = "SUCCESS" in result_str
    result = {
        "target": target,
        "search_folder": search_folder,
        "exists": exists,
        "status": "found" if exists else "notfound"
    }
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    # Local test loop
    async def main():
        if len(sys.argv) > 1:
            target = sys.argv[1]
            folder = sys.argv[2] if len(sys.argv) > 2 else "workspace"
            print(await check_file.ainvoke({"target": target, "search_folder": folder}))
        else:
            target = input("Enter the file name to check: ").strip()
            folder = input("Enter the folder to search in (press Enter for 'workspace'): ").strip() or "workspace"
            if target:
                print(await check_file.ainvoke({"target": target, "search_folder": folder}))

    asyncio.run(main())
