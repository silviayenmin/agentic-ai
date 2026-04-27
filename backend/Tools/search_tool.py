import os
import re
from typing import List, Dict, Any
from langchain_core.tools import tool
 
def _search_code_logic(query: str, extension: str = None, root_dir: str = ".") -> List[Dict[str, Any]]:
    """
    Internal logic for searching code.
    """
    results = []
    pattern = re.compile(query, re.IGNORECASE)
   
    for root, dirs, files in os.walk(root_dir):
        # Skip some common directories
        if any(ignored in root for ignored in ["venv", "__pycache__", ".git", "node_modules"]):
            continue
           
        for file in files:
            if extension:
                clean_ext = extension.lstrip('*').lstrip('.')
                if not file.endswith('.' + clean_ext) and not file.endswith(clean_ext):
                    continue
               
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if pattern.search(line):
                            results.append({
                                "file": os.path.relpath(file_path, root_dir).replace('\\', '/'),
                                "line": i,
                                "content": line.strip()
                            })
            except (UnicodeDecodeError, PermissionError):
                continue
               
    return results
 
@tool
def search_code(query: str, extension: str = None, root_dir: str = ".") -> List[Dict[str, Any]]:
    """
    Searches for a string or regex pattern in the codebase.
    Returns a list of matches with file path and line number.
    """
    return _search_code_logic(query, extension, root_dir)
 
def _find_file_logic(filename: str, root_dir: str = ".") -> List[str]:
    """
    Internal logic for finding files.
    """
    matches = []
    for root, dirs, files in os.walk(root_dir):
        if any(ignored in root for ignored in ["venv", "__pycache__", ".git", "node_modules"]):
            continue
        for file in files:
            if filename.lower() in file.lower():
                matches.append(os.path.relpath(os.path.join(root, file), root_dir).replace('\\', '/'))
    return matches
 
@tool
def find_file(filename: str, root_dir: str = ".") -> List[str]:
    """
    Finds the location of a file by its name (case-insensitive).
    """
    return _find_file_logic(filename, root_dir)
 
 