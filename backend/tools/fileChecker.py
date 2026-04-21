import os
import sys
from langchain_core.tools import tool

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

@tool
def check_file_exists(target: str, search_folder: str = 'workspace') -> bool:
    """
    Checks if a file exists in a specific folder.
    Supports both direct paths and recursive searching for filenames.
    """
    # Normalize path separators
    target = target.replace('\\', '/')
    
    # Check if it's a direct path starting from current directory
    if os.path.isfile(target):
        return True
    
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
                    return True
                
    return False

if __name__ == "__main__":
    # Keeping the original CLI functionality for backward compatibility
    search_folder = 'workspace'
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if len(sys.argv) > 2:
            search_folder = sys.argv[2]
    else:
        filename = input("Enter the file name to check: ").strip()
        folder_input = input("Enter the folder to search in (press Enter for 'workspace'): ").strip()
        if folder_input:
            search_folder = folder_input
    
    if filename and check_file_exists.run({"target": filename, "search_folder": search_folder}):
        print("found")
    else:
        print("notfound")
