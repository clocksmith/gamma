"""Solver backends that call the claude -p and codex exec harnesses (subscription auth).

Each call runs in a fresh, empty temporary directory with no tools:
- claude: --tools "" (all built-in tools disabled), no MCP servers, no setting
  sources, no session persistence, JSON output.
- codex: no switch disables its shell tool, so it runs ephemeral with a
  read-only sandbox, an explicit instruction not to run commands, and every
  non-message item in its JSON event stream is counted as tool use.

The routes use the same Generation interface as the local model. A token cap
cannot be enforced through either CLI; the wall-clock cap is enforced by
killing the process group. Usage, reported cost (notional on a subscription)
and tool use are recorded per call. Usage-limit and transport errors raise
SolverUnavailable so the runner stops cleanly and can resume later.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from .model import Generation
from .records import DATA

CALL_DIR_ROOT = DATA / "cli_calls"
NO_TOOLS_NOTE = "Do not run any commands or use any tools; answer directly from reasoning."
RETRIES = 2


class SolverUnavailable(RuntimeError):
    """Usage limit, auth or transport failure: stop the run; do not record a result."""


def render_conversation(messages: list[dict]) -> tuple[str, str]:
    """Flatten system/user/assistant turns into (system, prompt) for a stateless CLI call."""
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    turns = [m for m in messages if m["role"] != "system"]
    if len(turns) == 1:
        return system, turns[0]["content"]
    parts = [turns[0]["content"]]
    for message in turns[1:]:
        heading = "### Your previous answer" if message["role"] == "assistant" else "### Feedback"
        parts.append(f"{heading}\n{message['content']}")
    return system, "\n\n".join(parts)


def _run(argv: list[str], cwd: Path, timeout: float) -> tuple[int | None, str, str, float, bool]:
    started = time.perf_counter()
    proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True, stdin=subprocess.DEVNULL)
    try:
        out, err = proc.communicate(timeout=max(timeout, 1.0))
        timed_out = False
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        timed_out = True
    return proc.returncode, out, err, time.perf_counter() - started, timed_out


class _CLIGenerator:
    name = "cli"

    def __init__(self, model: str, effort: str) -> None:
        self.model = model
        self.effort = effort
        self.torch = None
        CALL_DIR_ROOT.mkdir(parents=True, exist_ok=True)

    def describe(self) -> dict:
        return {"harness": self.name, "model": self.model, "effort": self.effort, "tools": "none",
                "token_cap": "not enforceable through the CLI; recorded", "wall_cap": "enforced by process kill"}

    def generate(self, messages: list[dict], *, max_new_tokens: int, max_time: float) -> Generation:
        if max_time <= 1.0:
            return Generation("", 0, 0, 0.0, "max_time")
        deadline = time.perf_counter() + max_time
        last_error = ""
        for attempt in range(RETRIES + 1):
            remaining = deadline - time.perf_counter()
            if remaining <= 1.0:
                return Generation("", 0, 0, max_time, "max_time", meta={"last_error": last_error})
            workdir = Path(tempfile.mkdtemp(prefix=f"{self.name}-", dir=CALL_DIR_ROOT))
            try:
                result = self._call(messages, workdir, remaining)
            finally:
                shutil.rmtree(workdir, ignore_errors=True)
            if result is not None and not isinstance(result, str):
                return result
            last_error = result or "unknown error"
            if _looks_like_limit(last_error):
                raise SolverUnavailable(f"{self.name}: {last_error[:300]}")
            time.sleep(min(5 * (attempt + 1), max(deadline - time.perf_counter() - 1, 0)))
        raise SolverUnavailable(f"{self.name}: repeated failures: {last_error[:300]}")

    def _call(self, messages: list[dict], workdir: Path, timeout: float) -> Generation | str:
        raise NotImplementedError


def _looks_like_limit(text: str) -> bool:
    lowered = text.lower()
    return any(k in lowered for k in ("usage limit", "rate limit", "rate_limit", "429", "quota", "credit",
                                      "not logged in", "authentication", "unauthorized", "login"))


class ClaudeCLIGenerator(_CLIGenerator):
    name = "claude"

    def _call(self, messages, workdir, timeout):
        system, prompt = render_conversation(messages)
        argv = [
            "claude", "-p", "--output-format", "json", "--model", self.model, "--effort", self.effort,
            "--tools", "", "--strict-mcp-config", "--setting-sources", "", "--no-session-persistence",
            "--disable-slash-commands", "--system-prompt", system, prompt,
        ]
        code, out, err, seconds, timed_out = _run(argv, workdir, timeout)
        if timed_out:
            return Generation("", 0, 0, seconds, "max_time", meta={"harness": self.name})
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            return f"exit={code} unparseable output: {out[-300:]} {err[-300:]}"
        if data.get("is_error") or data.get("subtype") != "success":
            return f"error result: {str(data.get('result'))[:300]} {err[-200:]}"
        usage = data.get("usage") or {}
        input_tokens = (usage.get("input_tokens") or 0) + (usage.get("cache_read_input_tokens") or 0) + (
            usage.get("cache_creation_input_tokens") or 0)
        return Generation(
            text=data.get("result") or "",
            prompt_tokens=int(input_tokens),
            new_tokens=int(usage.get("output_tokens") or 0),
            seconds=seconds,
            stopped_by="eos",
            meta={
                "harness": self.name,
                "models": list((data.get("modelUsage") or {}).keys()),
                "num_turns": data.get("num_turns"),
                "duration_api_ms": data.get("duration_api_ms"),
                "reported_cost_usd": data.get("total_cost_usd"),
                "tool_items": max((data.get("num_turns") or 1) - 1, 0),
            },
        )


class CodexCLIGenerator(_CLIGenerator):
    name = "codex"

    def _call(self, messages, workdir, timeout):
        system, prompt = render_conversation(messages)
        last = workdir / "last_message.txt"
        full_prompt = f"{system}\n\n{NO_TOOLS_NOTE}\n\n{prompt}" if system else f"{NO_TOOLS_NOTE}\n\n{prompt}"
        argv = [
            "codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check", "-s", "read-only",
            "-m", self.model, "-c", f"model_reasoning_effort={self.effort}",
            "-C", str(workdir), "-o", str(last), full_prompt,
        ]
        code, out, err, seconds, timed_out = _run(argv, workdir, timeout)
        if timed_out:
            return Generation("", 0, 0, seconds, "max_time", meta={"harness": self.name})
        events = []
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        failures = [e for e in events if e.get("type") in ("turn.failed", "error")]
        completed = [e for e in events if e.get("type") == "turn.completed"]
        if failures or not completed:
            detail = json.dumps(failures[-1])[:300] if failures else f"exit={code} {err[-300:]}"
            return f"codex failed: {detail}"
        usage = completed[-1].get("usage") or {}
        items = [e.get("item") or {} for e in events if e.get("type") == "item.completed"]
        text = last.read_text(encoding="utf-8") if last.exists() else ""
        if not text:
            messages_out = [i.get("text", "") for i in items if i.get("type") == "agent_message"]
            text = messages_out[-1] if messages_out else ""
        return Generation(
            text=text,
            prompt_tokens=int(usage.get("input_tokens") or 0),
            new_tokens=int((usage.get("output_tokens") or 0) + (usage.get("reasoning_output_tokens") or 0)),
            seconds=seconds,
            stopped_by="eos",
            meta={
                "harness": self.name,
                "models": [self.model],
                "output_tokens": usage.get("output_tokens"),
                "reasoning_output_tokens": usage.get("reasoning_output_tokens"),
                "cached_input_tokens": usage.get("cached_input_tokens"),
                "tool_items": sum(1 for i in items if i.get("type") not in ("agent_message", "reasoning")),
                "item_types": sorted({i.get("type", "") for i in items}),
            },
        )


SOLVERS = {
    "claude": lambda: ClaudeCLIGenerator(model="claude-opus-5-5", effort="high"),
    "codex": lambda: CodexCLIGenerator(model="gpt-6-astra", effort="high"),
}
