"""
Quick sanity-check: directly invokes create_file_tool, write_to_file, and
check_file_exists via .ainvoke() — exactly as the executor does after the fix.

Run from backend/:
    python test_tools.py
"""
import asyncio
import sys
import os

# Ensure backend is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Tools
from langchain_core.tools import BaseTool


async def invoke(tool_obj, args: dict):
    """Call any tool the same way the fixed _run_tool does."""
    assert isinstance(tool_obj, BaseTool), f"{tool_obj} is not a BaseTool!"
    result = await tool_obj.ainvoke(args)
    return result


async def main():
    sep = "-" * 60

    # ── 1. create_file_tool ──────────────────────────────────────
    print(sep)
    print("TEST 1: create_file_tool")
    result = await invoke(
        Tools.create_file_tool,
        {"file_path": "manickam.js", "content": 'console.log("Hello World");'},
    )
    print("Result:", result)

    # ── 2. check_file_exists ─────────────────────────────────────
    print(sep)
    print("TEST 2: check_file_exists  (should find manickam.js)")
    result = await invoke(Tools.check_file_exists, {"target": "manickam.js"})
    print("Result:", result)

    # ── 3. write_to_file (overwrite) ─────────────────────────────
    print(sep)
    print("TEST 3: write_to_file  (overwrite with updated content)")
    result = await invoke(
        Tools.write_to_file,
        {"file_name": "manickam.js", "content": 'console.log("Hello World — updated!");'},
    )
    print("Result:", result)

    # ── 4. read_file_tool ────────────────────────────────────────
    print(sep)
    print("TEST 4: read_file_tool  (verify content — uses absolute path)")
    from config_loader import get_workspace_dir
    abs_path = os.path.join(get_workspace_dir(), "manickam.js")
    result = await invoke(Tools.read_file_tool, {"file_path": abs_path})
    print("Result:", result)

    # ── 5. Alias normalisation check ─────────────────────────────
    print(sep)
    print("TEST 5: write_to_file with aliased key 'file_path' (executor alias)")
    raw_args = {"file_path": "manickam_alias.js", "content": "// alias test"}
    _ALIASES = {"file_path": "file_name", "filename": "file_name"}
    normalised = {_ALIASES.get(k, k): v for k, v in raw_args.items()}
    print("Normalised args:", normalised)
    result = await invoke(Tools.write_to_file, normalised)
    print("Result:", result)

    # ── 6. create_file_tool  (already exists — should skip) ──────
    print(sep)
    print("TEST 6: create_file_tool on existing file (should skip, not overwrite)")
    result = await invoke(
        Tools.create_file_tool,
        {"file_path": "manickam.js", "content": "// SHOULD NOT APPEAR"},
    )
    print("Result:", result)

    print(sep)
    print("All tests complete. Check the 'output/' folder for the created files.")


if __name__ == "__main__":
    asyncio.run(main())
