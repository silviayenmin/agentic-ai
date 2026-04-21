import os
import re
from typing import List, Dict, Any
from langchain_core.tools import tool

@tool
def search_code(query: str, extension: str = None, root_dir: str = ".") -> List[Dict[str, Any]]:
    """
    Searches for a string or regex pattern in the codebase.
    Returns a list of matches with file path and line number.
    """
    results = []
    pattern = re.compile(query, re.IGNORECASE)
    
    for root, dirs, files in os.walk(root_dir):
        # Skip some common directories
        if any(ignored in root for ignored in ["venv", "__pycache__", ".git", "node_modules"]):
            continue
            
        for file in files:
            if extension and not file.endswith(extension):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if pattern.search(line):
                            results.append({
                                "file": os.path.relpath(file_path, root_dir),
                                "line": i,
                                "content": line.strip()
                            })
            except (UnicodeDecodeError, PermissionError):
                continue
                
    return results

@tool
def find_file(filename: str, root_dir: str = ".") -> List[str]:
    """
    Finds the location of a file by its name (case-insensitive).
    """
    matches = []
    for root, dirs, files in os.walk(root_dir):
        if any(ignored in root for ignored in ["venv", "__pycache__", ".git", "node_modules"]):
            continue
        for file in files:
            if filename.lower() in file.lower():
                matches.append(os.path.relpath(os.path.join(root, file), root_dir))
    return matches
