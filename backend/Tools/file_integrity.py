import os
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import sys

# Add parent directory to path to import config_loader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import get_workspace_dir

class IntegrityCheckInput(BaseModel):
    files: List[str] = Field(..., description="List of relative file paths to verify.")
    directories: List[str] = Field(default=[], description="List of relative directory paths to verify.")
    check_content: bool = Field(True, description="Whether to verify that files are not empty.")

@tool(args_schema=IntegrityCheckInput)
def verify_integrity(files: List[str], directories: List[str] = [], check_content: bool = True) -> str:
    """
    Verifies that specific files and directories exist and meet integrity standards (e.g., non-empty).
    Use this to confirm that a project was created successfully or a set of files were written correctly.
    """
    workspace = get_workspace_dir()
    results = []
    success_count = 0
    total_count = len(files) + len(directories)

    for d in directories:
        full_path = os.path.join(workspace, d)
        if os.path.exists(full_path) and os.path.isdir(full_path):
            results.append(f"[OK] Directory exists: {d}")
            success_count += 1
        else:
            results.append(f"[FAIL] Directory MISSING or not a folder: {d}")

    for f in files:
        full_path = os.path.join(workspace, f)
        if not os.path.exists(full_path):
            results.append(f"[FAIL] File MISSING: {f}")
        elif not os.path.isfile(full_path):
            results.append(f"[FAIL] Path exists but is NOT a file: {f}")
        else:
            if check_content:
                size = os.path.getsize(full_path)
                if size > 0:
                    results.append(f"[OK] File exists and has content ({size} bytes): {f}")
                    success_count += 1
                else:
                    results.append(f"[FAIL] File is EMPTY (0 bytes): {f}")
            else:
                results.append(f"[OK] File exists: {f}")
                success_count += 1

    status = "SUCCESS" if success_count == total_count else "FAILED"
    summary = f"Integrity Check: {status} ({success_count}/{total_count} items passed)"
    
    from logger import log
    log.verify("INTEGRITY", success_count == total_count, summary)

    return json.dumps({
        "summary": summary,
        "details": results,
        "status": status
    }, indent=2)
