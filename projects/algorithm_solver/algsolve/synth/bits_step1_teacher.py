"""The authorized BITS step 1 teacher: Claude Opus 5.5 through the `claude -p` CLI.

The CLI runs isolated: no tools, no MCP servers, no settings or session files, a
fixed system prompt. The prompt is the frozen template with the teacher's public
input (statement, starter code, parameter types, public examples) substituted;
its template hash must equal the authorized prompt_sha256. Every call is logged
with its timing, CLI version and reported cost. There is no retry and no
feedback from qualification: one call per problem.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

SYSTEM_PROMPT = ("You write programs in a small typed language behind an API. Reply with the single JSON "
                 "array the request asks for and nothing else: no prose, no code fences.")
PLACEHOLDER = "{{PUBLIC_INPUT}}"


def template_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _unfenced(text):
    text = str(text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def make_generate_fn(template_path, *, model, log_path, claude="claude", timeout=600):
    template = Path(template_path).read_text(encoding="utf-8")
    if template.count(PLACEHOLDER) != 1:
        raise ValueError("Teacher prompt template must contain the public input placeholder once")
    version = subprocess.run([claude, "--version"], capture_output=True, text=True, timeout=60).stdout.strip()
    log_path = Path(log_path)

    def generate(uid, isolated_input, plan_sha256, config):
        if config.get("prompt_sha256") != template_sha256(template_path):
            raise PermissionError("Teacher prompt differs from the authorized prompt hash")
        prompt = template.replace(PLACEHOLDER, json.dumps(isolated_input, sort_keys=True))
        env = {key: value for key, value in os.environ.items() if key != "CLAUDECODE"}
        started = time.monotonic()
        entry = {"uid": uid, "plan_sha256": plan_sha256, "model": model, "cli_version": version,
                 "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}
        try:
            completed = subprocess.run(
                [claude, "-p", "--model", model, "--output-format", "json", "--tools", "",
                 "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--setting-sources", "",
                 "--no-session-persistence", "--system-prompt", SYSTEM_PROMPT],
                input=prompt, capture_output=True, text=True, timeout=timeout, env=env)
            envelope = None
            try:
                envelope = json.loads(completed.stdout) if completed.stdout.strip() else None
            except json.JSONDecodeError:
                envelope = None
            if completed.returncode != 0 or (envelope or {}).get("is_error"):
                # The CLI reports failures such as an expired login in the stdout
                # envelope ("result"), often with an empty stderr.
                detail = (envelope or {}).get("result") or completed.stderr or completed.stdout
                raise RuntimeError(f"claude exited {completed.returncode}: {str(detail)[:300]}")
            entry.update(cost_usd=envelope.get("total_cost_usd"), is_error=envelope.get("is_error"))
            proposals = json.loads(_unfenced(envelope.get("result")))
            if not isinstance(proposals, list):
                raise ValueError("Teacher reply is not a JSON array")
            entry["proposals"] = len(proposals)
            return proposals
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as error:
            entry["error"] = f"{type(error).__name__}: {str(error)[:200]}"
            raise ValueError(entry["error"]) from error
        except Exception as error:
            entry["error"] = f"{type(error).__name__}: {str(error)[:200]}"
            raise
        finally:
            entry["seconds"] = round(time.monotonic() - started, 2)
            with log_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(entry, sort_keys=True) + "\n")

    return generate, version


def public_input_sha256(public_input):
    return hashlib.sha256(json.dumps(public_input, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def make_recorded_fn(path):
    """Teacher that replays proposals recorded by `bits_step1 teach`, bound to input hashes.

    A row is answered only when the adapter's public input hashes to the value
    recorded with the proposals; any difference blocks that row.
    """
    records = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["uid"] in records:
            raise ValueError(f"Duplicate recorded teacher output for {record['uid']}")
        records[record["uid"]] = record

    def generate(uid, isolated_input, plan_sha256, config):
        record = records.get(uid)
        if record is None:
            raise ValueError("No recorded teacher output for this problem")
        if record["public_input_sha256"] != public_input_sha256(isolated_input):
            raise PermissionError("Recorded teacher output was produced for a different public input")
        if record["plan_sha256"] != plan_sha256 or record["prompt_sha256"] != config.get("prompt_sha256"):
            raise PermissionError("Recorded teacher output is bound to a different plan or prompt")
        if record.get("error"):
            raise ValueError("Recorded teacher call failed: " + record["error"])
        return record["proposals"]

    return generate, records
