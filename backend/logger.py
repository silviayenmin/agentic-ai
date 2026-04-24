"""
logger.py — Centralized structured logger for the Agentic AI backend.

Usage:
    from logger import log

    log.tool_ok("write_to_file", "manickam.js written")
    log.tool_fail("read_file_tool", "file not found")
    log.agent_start("Executor")
    log.agent_ok("Executor", "task complete")
    log.agent_fail("Executor", "tool crashed")
    log.step("Planner", "Building plan from analysis...")
    log.retry("Executor", attempt=2, max=5)
    log.warn("CodeEvaluator", "response was empty, retrying tool loop")
    log.info("MasterAgent", "Routing → CODING")
"""

import sys
import traceback
from datetime import datetime

# Windows terminal emoji support
if sys.platform == "win32":
    try:
        import sys
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        pass

def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")

def _fmt(icon: str, tag: str, name: str, msg: str) -> str:
    # Use a safe return that handles potential encoding issues if reconfigure failed
    line = f"{icon}  [{_ts()}] [{tag}] {name} — {msg}"
    return line


class _Logger:
    # ── Tools ─────────────────────────────────────────────────────
    def tool_ok(self, tool_name: str, detail: str = ""):
        msg = f"Tool '{tool_name}' succeeded"
        if detail:
            msg += f" → {detail}"
        print(_fmt("✅", "TOOL ", tool_name, msg))

    def tool_fail(self, tool_name: str, detail: str = "", exc: Exception = None):
        msg = f"Tool '{tool_name}' FAILED"
        if detail:
            msg += f" → {detail}"
        print(_fmt("❌", "TOOL ", tool_name, msg))
        if exc:
            print(f"   └─ {type(exc).__name__}: {exc}")
            print("   " + "\n   ".join(traceback.format_exc().splitlines()))

    def tool_skip(self, tool_name: str, reason: str = ""):
        msg = f"Tool '{tool_name}' skipped"
        if reason:
            msg += f" ({reason})"
        print(_fmt("⏭️ ", "TOOL ", tool_name, msg))

    def tool_call(self, tool_name: str, args: dict):
        print(_fmt("🔧", "TOOL ", tool_name, f"Invoking with args: {args}"))

    def tool_result(self, tool_name: str, result: str):
        # Print tool output in a readable indented block
        lines = result.strip().splitlines()
        if len(lines) > 20:
            content = "\n".join(lines[:10]) + f"\n... ({len(lines)-20} more lines) ...\n" + "\n".join(lines[-10:])
        else:
            content = "\n".join(lines)
            
        indented = "   │ " + "\n   │ ".join(content.splitlines())
        print(f"   ┌── [RESULT: {tool_name}] ──────────────────")
        print(indented)
        print("   └────────────────────────────────────────────")

    # ── Agents ────────────────────────────────────────────────────
    def agent_start(self, agent_name: str, task: str = ""):
        msg = f"Agent '{agent_name}' starting"
        if task:
            msg += f" → {task}"
        print(_fmt("🚀", "AGENT", agent_name, msg))

    def agent_ok(self, agent_name: str, detail: str = ""):
        msg = f"Agent '{agent_name}' completed"
        if detail:
            msg += f" → {detail}"
        print(_fmt("✅", "AGENT", agent_name, msg))

    def agent_fail(self, agent_name: str, detail: str = "", exc: Exception = None):
        msg = f"Agent '{agent_name}' FAILED"
        if detail:
            msg += f" → {detail}"
        print(_fmt("❌", "AGENT", agent_name, msg))
        if exc:
            print(f"   └─ {type(exc).__name__}: {exc}")

    # ── LLM calls ────────────────────────────────────────────────
    def llm_call(self, agent_name: str, attempt: int, workflow_attempt: int):
        suffix = f" (Internal Retry {attempt - 1})" if attempt > 1 else ""
        print(_fmt("🤖", "LLM  ", agent_name, f"Attempt {workflow_attempt}{suffix}: sending prompt..."))

    def llm_ok(self, agent_name: str, attempt: int):
        print(_fmt("✅", "LLM  ", agent_name, f"Attempt {attempt} response received"))

    def llm_fail(self, agent_name: str, attempt: int, max_retries: int, exc: Exception):
        print(_fmt("❌", "LLM  ", agent_name, f"Attempt {attempt}/{max_retries} failed — {type(exc).__name__}: {exc}"))

    def llm_retry(self, agent_name: str, wait: int):
        print(_fmt("⏳", "LLM  ", agent_name, f"Retrying in {wait}s..."))

    def llm_exhausted(self, agent_name: str, max_retries: int):
        print(_fmt("❌", "LLM  ", agent_name, f"All {max_retries} attempts exhausted — raising error"))

    # ── Workflow routing ──────────────────────────────────────────
    def route(self, from_node: str, to_node: str, reason: str = ""):
        msg = f"Routing {from_node} → {to_node}"
        if reason:
            msg += f" ({reason})"
        print(_fmt("🔀", "ROUTE", from_node, msg))

    def retry(self, agent_name: str, attempt: int, max_attempts: int):
        print(_fmt("🔁", "RETRY", agent_name, f"Retry {attempt}/{max_attempts}"))

    # ── General ───────────────────────────────────────────────────
    def step(self, agent_name: str, msg: str):
        print(_fmt("📌", "STEP ", agent_name, msg))

    def info(self, agent_name: str, msg: str):
        print(_fmt("ℹ️ ", "INFO ", agent_name, msg))

    def warn(self, agent_name: str, msg: str):
        print(_fmt("⚠️ ", "WARN ", agent_name, msg))

    def persist(self, label: str, msg: str):
        print(_fmt("💾", "STORE", label, msg))


# Singleton
log = _Logger()
