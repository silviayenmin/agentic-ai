import os
import subprocess
import json
import signal
import psutil
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Global dictionary to track active processes started by the agent
# In a production environment, this might be persisted in a DB
active_processes: Dict[int, subprocess.Popen] = {}

class RunCommandInput(BaseModel):
    command: str = Field(..., description="The command to run (e.g., 'npm start', 'npm run dev', 'python main.py')")
    path: str = Field(..., description="The directory path where the command should be executed.")
    is_background: bool = Field(True, description="Whether to run as a background process (standard for servers).")

class StopProcessInput(BaseModel):
    pid: Optional[int] = Field(None, description="The Process ID to terminate.")
    command_name: Optional[str] = Field(None, description="If PID is unknown, search for processes with this name (e.g., 'npm').")

def get_process_info(proc: subprocess.Popen) -> Dict[str, Any]:
    return {
        "pid": proc.pid,
        "status": "running" if proc.poll() is None else "finished/error",
        "return_code": proc.return_code
    }

@tool(args_schema=RunCommandInput)
def execute_command(command: str, path: str, is_background: bool = True) -> str:
    """
    Executes a shell command in a specific directory. 
    Ideal for starting servers (npm start) or running scripts.
    """
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        return json.dumps({"error": f"Path not found: {abs_path}"})

    try:
        if is_background:
            # Start process in background
            # shell=True is needed for 'npm' on Windows
            process = subprocess.Popen(
                command,
                cwd=abs_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            active_processes[process.pid] = process
            
            # Read a bit of output to see if it crashed immediately
            try:
                # Use a small timeout to not block
                stdout, stderr = process.communicate(timeout=2)
                output = stdout + stderr
            except subprocess.TimeoutExpired:
                output = "Process started and is running in background."

            return json.dumps({
                "message": "Background process started.",
                "process_info": get_process_info(process),
                "initial_output": output[:500] # Return first 500 chars
            }, indent=2)
        else:
            # Run and wait for completion
            result = subprocess.run(
                command,
                cwd=abs_path,
                shell=True,
                capture_output=True,
                text=True
            )
            return json.dumps({
                "status": "completed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@tool(args_schema=StopProcessInput)
def stop_process(pid: Optional[int] = None, command_name: Optional[str] = None) -> str:
    """
    Terminates a running process by PID or searches for it by command name.
    Useful for stopping development servers.
    """
    terminated = []
    
    if pid and pid in active_processes:
        proc = active_processes.pop(pid)
        try:
            # On Windows, we need to kill the process tree for 'npm'
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            terminated.append(pid)
        except Exception as e:
            return json.dumps({"error": f"Failed to kill PID {pid}: {str(e)}"})

    elif command_name:
        # Search for processes matching the name
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if command_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    terminated.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
    return json.dumps({
        "status": "success" if terminated else "no_process_found",
        "terminated_pids": terminated
    }, indent=2)
