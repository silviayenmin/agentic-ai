import os
from pathlib import Path
from typing import Optional

def create_file_if_not_exists(file_path: str, content: str = "") -> str:
    """
    Creates a new file if it does not already exist, ensuring the operation 
    can proceed without errors or interruptions.
    
    Args:
        file_path (str): The path to the file to be created.
        content (str): The initial content of the file if created. Defaults to empty string.
        
    Returns:
        str: A status message indicating the result of the operation.
    """
    try:
        # Normalize the path for the current OS
        path = Path(file_path).resolve()
        
        # Check if the file already exists
        if path.exists():
            if path.is_file():
                return f"File already exists: {file_path}. No action taken."
            else:
                return f"Error: Path exists but is a directory: {file_path}."
        
        # Ensure parent directories exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create the file with provided content
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"Successfully created file: {file_path}"
        
    except PermissionError:
        return f"Error: Permission denied when attempting to create {file_path}."
    except OSError as e:
        return f"Error: OS error occurred while creating {file_path}: {e.strerror}"
    except Exception as e:
        return f"Error: An unexpected error occurred: {str(e)}"

if __name__ == "__main__":
    # Quick internal test
    test_file = "workspace/test_creation.txt"
    print(create_file_if_not_exists(test_file, "This is a test file content."))
    print(create_file_if_not_exists(test_file, "This should not overwrite."))
