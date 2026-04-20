import os
import ctypes
import platform
import json
import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class OSPermissionInput(BaseModel):
    """Input schema for requesting OS permissions."""

    action: str = Field(
        ...,
        description="The sensitive OS action to be performed (e.g., 'install_package', 'delete_system_dir', 'modify_registry').",
    )
    reason: str = Field(
        ...,
        description="The reason why this permission is required for the agent to proceed.",
    )
    timeout: int = Field(
        60, description="How many seconds to wait for human approval before timing out."
    )


def is_admin() -> bool:
    """Checks if the current process has administrative/root privileges."""
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.getuid() == 0
    except AttributeError:
        return False


async def wait_for_human_approval(
    action: str, reason: str, timeout: int
) -> Dict[str, Any]:
    """
    Simulates or integrates with a Human-In-The-Loop approval system.
    In a real implementation, this would:
    1. Send a WebSocket message to the UI.
    2. Wait for a response in a shared state/DB.
    """
    print(f"\n[HIL REQUEST] Action: {action}")
    print(f"[HIL REQUEST] Reason: {reason}")
    print(f"[HIL REQUEST] Waiting up to {timeout}s for human approval...")

    # This is a placeholder for the actual HIL logic.
    # In your FastAPI app, you would likely poll a database or wait on an asyncio.Event.
    # For now, we simulate a 'PENDING' state that requires external intervention.

    # Example:
    # return await approval_manager.ask(action, reason, timeout)

    return {
        "status": "pending_manual_approval",
        "message": "The agent is requesting permission to perform a sensitive operation. Please approve via the dashboard.",
        "action": action,
        "is_admin_process": is_admin(),
    }


@tool(args_schema=OSPermissionInput)
async def request_os_permission(action: str, reason: str, timeout: int = 60) -> str:
    """
    Requests permission from a human operator to perform sensitive OS-level operations.
    Follows the Human-In-The-Loop (HIL) concept.
    """
    # First check if we already have admin rights (some permissions might be implicit)
    admin_status = is_admin()

    # If it's a simple check or if we already have rights, we might skip HIL,
    # but usually HIL is about policy, not just capability.

    result = await wait_for_human_approval(action, reason, timeout)

    return json.dumps(result, indent=2)


# if __name__ == "__main__":
#     # Local test
#     async def test():
#         print(f"Running as Admin: {is_admin()}")
#         res = await request_os_permission.ainvoke({
#             "action": "delete_logs",
#             "reason": "Clear disk space for new project logs.",
#             "timeout": 30
#         })
#         print("\nTool Output:")
#         print(res)

#     asyncio.run(test())
