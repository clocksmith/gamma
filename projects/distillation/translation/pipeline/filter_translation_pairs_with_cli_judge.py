#!/usr/bin/env python3
"""Filter EN/ES translation pair JSONL data through a host CLI LLM judge."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shlex
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUT_DIR = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "cli_judge_filter"
)
DEFAULT_PREFIX = "cli_judge_filter"
VALID_DECISIONS = {"keep", "drop", "rewrite", "review"}
VALID_ROUTES = {"keep", "drop", "review"}
JUDGE_PROFILE_INSTRUCTIONS = {
    "balanced": (
        "Prefer literal adequacy, preserved names, numbers, dates, units, negation, tense, and punctuation intent. "
        "Drop rows with wrong direction, hallucinated details, missing clauses, copied source, broken grammar, or "
        "target_pos matching target_neg."
    ),
    "strict_literal": (
        "Use external benchmark standards. Keep only rows whose target is a direct, complete, reference-like translation. "
        "Reject loose paraphrases that erase terms, clauses, modality, negation, dates, numbers, named entities, or units."
    ),
    "entity_guard": (
        "Focus on preservation of proper names, organizations, places, dates, numbers, percentages, units, times, and IDs. "
        "If any such item changes, disappears, or appears from nowhere, drop the row even if the rest is fluent."
    ),
    "external_wmt": (
        "Favor general-domain WMT-like references over synthetic template style. Penalize awkward literal calques, "
        "over-templated business boilerplate, and translations that sound unlike a natural external benchmark reference."
    ),
    "rewrite_surgeon": (
        "Keep strong rows. For rows with one small fixable issue, choose rewrite and provide corrected_target. "
        "Drop rows needing broad rewriting or with uncertain source-target alignment."
    ),
    "adversarial": (
        "Act as an adversarial data auditor. Look for copied source text, target_neg leakage, wrong language, missing "
        "clauses, swapped roles, tense drift, polite-form drift, and fluent hallucinations. Keep only rows that survive."
    ),
}


@dataclass(frozen=True)
class CallerOutput:
    stdout: str
    raw_stdout: str
    stderr: str
    returncode: int | None
    timed_out: bool
    command_argv: list[str]
    stdout_source: str


class CodexCLICaller:
    """Small non-shell wrapper for Codex, Claude, or another host CLI command."""

    def __init__(
        self,
        *,
        command: str,
        prompt_mode: str,
        timeout_sec: float,
        cwd: Path,
        artifacts_dir: Path,
    ) -> None:
        self.command = command
        self.command_argv = shlex.split(command)
        if not self.command_argv:
            raise RuntimeError("--command must not be empty")
        self.prompt_mode = prompt_mode
        self.timeout_sec = float(timeout_sec)
        self.cwd = cwd
        self.prompt_dir = artifacts_dir / "prompts"
        self.response_dir = artifacts_dir / "responses"
        self.prompt_dir.mkdir(parents=True, exist_ok=True)
        self.response_dir.mkdir(parents=True, exist_ok=True)

    def call(self, *, prompt: str, slug: str) -> CallerOutput:
        prompt_file = self.prompt_dir / f"{slug}.prompt.txt"
        response_file = self.response_dir / f"{slug}.response.txt"
        argv = [
            item.replace("{prompt_file}", str(prompt_file)).replace("{response_file}", str(response_file))
            for item in self.command_argv
        ]
        input_text: str | None = None

        if self.prompt_mode == "stdin":
            input_text = prompt
        elif self.prompt_mode == "arg":
            replaced = False
            next_argv: list[str] = []
            for item in argv:
                if "{prompt}" in item:
                    next_argv.append(item.replace("{prompt}", prompt))
                    replaced = True
                else:
                    next_argv.append(item)
            argv = next_argv if replaced else [*argv, prompt]
        elif self.prompt_mode == "file":
            prompt_file.write_text(prompt, encoding="utf-8")
            if not any("{prompt_file}" in item for item in self.command_argv):
                argv.append(str(prompt_file))
        else:
            raise RuntimeError(f"unsupported prompt mode: {self.prompt_mode}")

        try:
            completed = subprocess.run(
                argv,
                input=input_text,
                text=True,
                capture_output=True,
                timeout=self.timeout_sec,
                cwd=str(self.cwd),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return CallerOutput(
                stdout=_as_text(exc.stdout),
                raw_stdout=_as_text(exc.stdout),
                stderr=_as_text(exc.stderr),
                returncode=None,
                timed_out=True,
                command_argv=argv,
                stdout_source="stdout",
            )

        raw_stdout = completed.stdout or ""
        stdout = raw_stdout
        stdout_source = "stdout"
        if response_file.is_file():
            file_text = response_file.read_text(encoding="utf-8")
            if file_text.strip():
                stdout = file_text
                stdout_source = "response_file"
        return CallerOutput(
            stdout=stdout,
            raw_stdout=raw_stdout,
            stderr=completed.stderr or "",
            returncode=completed.returncode,
            timed_out=False,
            command_argv=argv,
            stdout_source=stdout_source,
        )


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="Input translation-pair JSONL.")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--prefix", default=DEFAULT_PREFIX)
    ap.add_argument("--command", default="", help="Host command, split with shlex and run without a shell.")
    ap.add_argument(
        "--prompt-mode",
        choices=["stdin", "arg", "file"],
        default="stdin",
        help="How to pass the row judge prompt to the host command.",
    )
    ap.add_argument("--timeout-sec", type=float, default=180.0)
    ap.add_argument("--cwd", default=str(PROJECT_ROOT))
    ap.add_argument("--limit", type=int, default=0, help="Maximum rows to process; 0 means all rows.")
    ap.add_argument("--start-index", type=int, default=0, help="Zero-based input row offset.")
    ap.add_argument("--resume", action="store_true", help="Reuse matching receipts from the output directory.")
    ap.add_argument(
        "--judge-profile",
        choices=sorted(JUDGE_PROFILE_INSTRUCTIONS),
        default="balanced",
        help="Built-in judge prompt profile.",
    )
    ap.add_argument(
        "--extra-instruction",
        default="",
        help="Additional profile instruction appended to the row judge prompt.",
    )
    ap.add_argument(
        "--rewrite-mode",
        choices=["queue", "apply", "off"],
        default="queue",
        help="What to do with judge-supplied corrected_target values.",
    )
    ap.add_argument("--include-judge-metadata", action="store_true")
    ap.add_argument("--min-adequacy", type=float, default=4.0)
    ap.add_argument("--min-literalness", type=float, default=3.5)
    ap.add_argument("--min-entity-number-preservation", type=float, default=4.0)
    ap.add_argument("--min-confidence", type=float, default=0.55)
    ap.add_argument(
        "--on-error",
        choices=["review", "drop", "keep"],
        default="review",
        help="Route rows here when the CLI fails or emits unparsable output.",
    )
    ap.add_argument(
        "--mock-decision",
        choices=sorted(VALID_DECISIONS),
        default="",
        help="Skip the host command and emit deterministic mock judge decisions.",
    )
    ap.add_argument("--mock-corrected-target", default="")
    ap.add_argument("--max-receipt-text-chars", type=int, default=12000)
    return ap.parse_args()


def _now_utc() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _resolve(path_text: str | Path) -> Path:
    path = Path(str(path_text).strip())
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _safe_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run_config_hash(args: argparse.Namespace) -> str:
    payload = {
        "command": "mock" if args.mock_decision else str(args.command),
        "mock_decision": str(args.mock_decision),
        "prompt_mode": str(args.prompt_mode),
        "judge_profile": str(args.judge_profile),
        "extra_instruction": str(args.extra_instruction),
        "rewrite_mode": str(args.rewrite_mode),
        "on_error": str(args.on_error),
        "thresholds": {
            "min_adequacy": float(args.min_adequacy),
            "min_literalness": float(args.min_literalness),
            "min_entity_number_preservation": float(args.min_entity_number_preservation),
            "min_confidence": float(args.min_confidence),
        },
    }
    return _hash_text(json.dumps(payload, sort_keys=True))


def _norm_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _row_id(row: dict[str, Any]) -> str:
    existing = _norm_text(row.get("row_id"))
    if existing:
        return existing
    payload = {
        "src_lang": _norm_text(row.get("src_lang")),
        "tgt_lang": _norm_text(row.get("tgt_lang")),
        "source": _norm_text(row.get("source")),
        "target_pos": _norm_text(row.get("target_pos")),
        "target_neg": _norm_text(row.get("target_neg")),
    }
    return _hash_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def _canonical_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if not _norm_text(out.get("source")) and _norm_text(out.get("query")):
        out["source"] = _norm_text(out.get("query"))
    if not _norm_text(out.get("target_pos")) and _norm_text(out.get("pos")):
        out["target_pos"] = _norm_text(out.get("pos"))
    if not _norm_text(out.get("target_neg")) and _norm_text(out.get("neg")):
        out["target_neg"] = _norm_text(out.get("neg"))

    pair = _norm_text(out.get("pair"))
    if pair and "-" in pair:
        src_lang, tgt_lang = pair.split("-", 1)
        if not _norm_text(out.get("src_lang")):
            out["src_lang"] = src_lang
        if not _norm_text(out.get("tgt_lang")):
            out["tgt_lang"] = tgt_lang
    src_lang = _norm_text(out.get("src_lang"))
    tgt_lang = _norm_text(out.get("tgt_lang"))
    if src_lang and tgt_lang:
        out["pair"] = f"{src_lang}-{tgt_lang}"
    if tgt_lang:
        out.setdefault("lang", tgt_lang)
    if _norm_text(out.get("source")):
        out.setdefault("query", out["source"])
    if _norm_text(out.get("target_pos")):
        out.setdefault("pos", out["target_pos"])
    if _norm_text(out.get("target_neg")):
        out.setdefault("neg", out["target_neg"])
    out["row_id"] = _row_id(out)
    return out


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"invalid JSONL at {path}:{line_no}: {exc}") from exc
            if not isinstance(row, dict):
                raise RuntimeError(f"expected object row at {path}:{line_no}")
            rows.append(_canonical_row(row))
    if not rows:
        raise RuntimeError(f"dataset is empty: {path}")
    return rows


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _trim(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[truncated]"


def _slug(line_index: int, row: dict[str, Any]) -> str:
    row_id = _row_id(row)
    return f"{line_index:06d}_{re.sub(r'[^0-9A-Za-z_.-]+', '_', row_id[:24])}"


def _judge_prompt(row: dict[str, Any], *, judge_profile: str, extra_instruction: str) -> str:
    prompt_row = {
        "row_id": row.get("row_id", ""),
        "pair": row.get("pair", ""),
        "src_lang": row.get("src_lang", ""),
        "tgt_lang": row.get("tgt_lang", ""),
        "source": row.get("source", ""),
        "target_pos": row.get("target_pos", ""),
        "target_neg": row.get("target_neg", ""),
        "source_file": row.get("source_file", row.get("source_path", "")),
    }
    schema = {
        "decision": "keep | drop | rewrite | review",
        "direction_ok": True,
        "meaning_preserved": True,
        "scores": {
            "adequacy": "0..5",
            "literalness": "0..5",
            "fluency": "0..5",
            "entity_number_preservation": "0..5",
            "external_eval_style": "0..5",
        },
        "issues": [],
        "corrected_target": "",
        "confidence": "0..1",
    }
    profile_instruction = JUDGE_PROFILE_INSTRUCTIONS.get(judge_profile, JUDGE_PROFILE_INSTRUCTIONS["balanced"])
    extra = _norm_text(extra_instruction)
    if extra:
        profile_instruction = f"{profile_instruction} Additional instruction: {extra}"
    return (
        "You are filtering one EN<->ES translation training row for distilling a 1B student.\n"
        "Judge whether target_pos is a faithful, reference-like translation of source in the requested direction.\n"
        f"Judge profile: {judge_profile}.\n"
        f"Profile instruction: {profile_instruction}\n"
        "Use rewrite only when a small corrected target would make the row usable.\n"
        "Return exactly one JSON object and no prose.\n\n"
        "Required JSON shape:\n"
        f"{json.dumps(schema, indent=2, ensure_ascii=False)}\n\n"
        "Row:\n"
        f"{json.dumps(prompt_row, indent=2, ensure_ascii=False)}\n"
    )


def _mock_judge(decision: str, corrected_target: str) -> dict[str, Any]:
    return {
        "decision": decision,
        "direction_ok": decision != "drop",
        "meaning_preserved": decision != "drop",
        "scores": {
            "adequacy": 5.0 if decision != "drop" else 1.0,
            "literalness": 5.0 if decision != "drop" else 1.0,
            "fluency": 5.0 if decision != "drop" else 1.0,
            "entity_number_preservation": 5.0 if decision != "drop" else 1.0,
            "external_eval_style": 5.0 if decision != "drop" else 1.0,
        },
        "issues": [] if decision != "drop" else ["mock_drop"],
        "corrected_target": corrected_target,
        "confidence": 1.0,
    }


def _extract_json_blob(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        for key in ("result", "message", "content", "last_message", "text"):
            value = parsed.get(key)
            if isinstance(value, str) and "{" in value:
                return _extract_json_blob(value)
        return stripped

    start = stripped.find("{")
    if start < 0:
        raise RuntimeError("no JSON object found")
    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(stripped)):
        char = stripped[idx]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return stripped[start : idx + 1]
    raise RuntimeError("unterminated JSON object")


def _parse_judge_json(text: str) -> dict[str, Any]:
    candidates = [text]
    jsonl_lines = [line for line in text.splitlines() if line.strip().startswith("{")]
    candidates.extend(reversed(jsonl_lines))
    last_error: Exception | None = None
    for candidate in candidates:
        try:
            blob = _extract_json_blob(candidate)
            parsed = json.loads(blob)
        except Exception as exc:
            last_error = exc
            continue
        if isinstance(parsed, dict):
            return _normalize_judge(parsed)
    raise RuntimeError(f"could not parse judge JSON: {last_error}")


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None


def _normalize_judge(raw: dict[str, Any]) -> dict[str, Any]:
    scores = raw.get("scores")
    if not isinstance(scores, dict):
        scores = {}
    normalized_scores = {
        "adequacy": _float_or_none(scores.get("adequacy", raw.get("adequacy"))),
        "literalness": _float_or_none(scores.get("literalness", raw.get("literalness"))),
        "fluency": _float_or_none(scores.get("fluency", raw.get("fluency"))),
        "entity_number_preservation": _float_or_none(
            scores.get("entity_number_preservation", raw.get("entity_number_preservation"))
        ),
        "external_eval_style": _float_or_none(scores.get("external_eval_style", raw.get("external_eval_style"))),
    }
    issues = raw.get("issues", [])
    if isinstance(issues, str):
        issues = [issues]
    if not isinstance(issues, list):
        issues = [str(issues)]
    decision = str(raw.get("decision", "review")).strip().lower()
    if decision not in VALID_DECISIONS:
        decision = "review"
    return {
        "decision": decision,
        "direction_ok": _bool_or_none(raw.get("direction_ok")),
        "meaning_preserved": _bool_or_none(raw.get("meaning_preserved")),
        "scores": normalized_scores,
        "issues": [str(item) for item in issues if str(item).strip()],
        "corrected_target": _norm_text(raw.get("corrected_target")),
        "confidence": _float_or_none(raw.get("confidence")),
    }


def _score_below(scores: dict[str, Any], key: str, threshold: float) -> bool:
    value = _float_or_none(scores.get(key))
    return value is not None and value < threshold


def _missing_required_score(scores: dict[str, Any], key: str) -> bool:
    return _float_or_none(scores.get(key)) is None


def _route_judge(
    *,
    judge: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[str, list[str], str]:
    reasons: list[str] = []
    decision = str(judge.get("decision", "review"))
    scores = judge.get("scores") if isinstance(judge.get("scores"), dict) else {}
    corrected_target = _norm_text(judge.get("corrected_target"))

    if decision == "drop":
        reasons.append("judge_drop")
    if judge.get("direction_ok") is False:
        reasons.append("direction_not_ok")
    if judge.get("meaning_preserved") is False:
        reasons.append("meaning_not_preserved")
    for key, threshold in (
        ("adequacy", float(args.min_adequacy)),
        ("literalness", float(args.min_literalness)),
        ("entity_number_preservation", float(args.min_entity_number_preservation)),
    ):
        if _missing_required_score(scores, key):
            reasons.append(f"missing_{key}")
        elif _score_below(scores, key, threshold):
            reasons.append(f"low_{key}")

    confidence = _float_or_none(judge.get("confidence"))
    low_confidence = confidence is None or confidence < float(args.min_confidence)
    if low_confidence:
        reasons.append("low_confidence")

    hard_fail = any(
        (reason.startswith("low_") and reason != "low_confidence")
        or reason.startswith("missing_")
        or reason in {"judge_drop", "direction_not_ok", "meaning_not_preserved"}
        for reason in reasons
    )
    if hard_fail:
        return "drop", reasons, ""
    if decision == "review":
        reasons.append("judge_review")
        return "review", reasons, ""
    if decision == "rewrite":
        if not corrected_target:
            reasons.append("rewrite_without_corrected_target")
            return "review", reasons, ""
        if args.rewrite_mode == "apply":
            reasons.append("rewrite_applied")
            return "keep", reasons, corrected_target
        if args.rewrite_mode == "queue":
            reasons.append("rewrite_queued")
            return "review", reasons, corrected_target
        reasons.append("rewrite_disabled")
        return "review", reasons, corrected_target
    if low_confidence:
        return "review", reasons, ""
    return "keep", reasons, ""


def _error_route(args: argparse.Namespace, reason: str) -> tuple[str, list[str], str]:
    route = str(args.on_error)
    if route not in VALID_ROUTES:
        route = "review"
    return route, [reason], ""


def _annotate(row: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["_cli_judge_filter"] = {
        "route": receipt["route"],
        "route_reasons": receipt["route_reasons"],
        "judge": receipt.get("judge", {}),
        "receipt_key": receipt["receipt_key"],
    }
    return out


def _apply_rewrite(row: dict[str, Any], corrected_target: str) -> dict[str, Any]:
    out = dict(row)
    out["target_pos"] = corrected_target
    out["pos"] = corrected_target
    out["row_id"] = _row_id(out)
    return out


def _load_receipt_cache(path: Path) -> dict[tuple[int, str, str, str], dict[str, Any]]:
    cache: dict[tuple[int, str, str, str], dict[str, Any]] = {}
    if not path.is_file():
        return cache
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                receipt = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (
                int(receipt.get("line_index", -1)),
                str(receipt.get("row_id", "")),
                str(receipt.get("prompt_hash", "")),
                str(receipt.get("run_config_hash", "")),
            )
            if key[0] >= 0 and key[1] and key[2] and key[3]:
                cache[key] = receipt
    return cache


def _build_receipt(
    *,
    line_index: int,
    row: dict[str, Any],
    prompt: str,
    output: CallerOutput | None,
    judge: dict[str, Any],
    route: str,
    route_reasons: list[str],
    corrected_target: str,
    args: argparse.Namespace,
    reused: bool = False,
    parse_error: str = "",
) -> dict[str, Any]:
    stdout = output.stdout if output else json.dumps(judge, ensure_ascii=False)
    raw_stdout = output.raw_stdout if output else stdout
    stderr = output.stderr if output else ""
    command_argv = output.command_argv if output else ["mock", str(args.mock_decision)]
    returncode = output.returncode if output else 0
    timed_out = output.timed_out if output else False
    stdout_source = output.stdout_source if output else "mock"
    row_id = _row_id(row)
    return {
        "receipt_key": f"{line_index}:{row_id}",
        "line_index": line_index,
        "row_id": row_id,
        "pair": row.get("pair", ""),
        "source_hash": _hash_text(_norm_text(row.get("source"))),
        "target_hash": _hash_text(_norm_text(row.get("target_pos"))),
        "prompt_hash": _hash_text(prompt),
        "run_config_hash": _run_config_hash(args),
        "response_hash": _hash_text(stdout),
        "generated_utc": _now_utc(),
        "command_argv": command_argv,
        "prompt_mode": args.prompt_mode,
        "stdout_source": stdout_source,
        "returncode": returncode,
        "timed_out": timed_out,
        "reused": bool(reused),
        "parse_error": parse_error,
        "route": route,
        "route_reasons": route_reasons,
        "corrected_target": corrected_target,
        "judge": judge,
        "stdout": _trim(stdout, int(args.max_receipt_text_chars)),
        "raw_stdout": _trim(raw_stdout, int(args.max_receipt_text_chars)),
        "stderr": _trim(stderr, int(args.max_receipt_text_chars)),
    }


def _write_summary_md(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# CLI Judge Filter Summary",
        "",
        f"- generated_utc: `{summary['generated_utc']}`",
        f"- input: `{summary['input']}`",
        f"- processed_rows: `{summary['processed_rows']}`",
        f"- command: `{summary['command']}`",
        f"- prompt_mode: `{summary['prompt_mode']}`",
        f"- judge_profile: `{summary['judge_profile']}`",
        f"- rewrite_mode: `{summary['rewrite_mode']}`",
        "",
        "## Routes",
        "",
        "| route | rows |",
        "| --- | ---: |",
    ]
    for route, count in sorted(summary["route_counts"].items()):
        lines.append(f"| {route} | {count} |")
    lines.extend(
        [
            "",
            "## Reason Counts",
            "",
            "| reason | rows |",
            "| --- | ---: |",
        ]
    )
    for reason, count in sorted(summary["reason_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {reason} | {count} |")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- filtered: `{summary['outputs']['filtered']}`",
            f"- rejected: `{summary['outputs']['rejected']}`",
            f"- review: `{summary['outputs']['review']}`",
            f"- rewrite_queue: `{summary['outputs']['rewrite_queue']}`",
            f"- receipts: `{summary['outputs']['receipts']}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    input_path = _resolve(str(args.input))
    out_dir = _resolve(str(args.out_dir))
    cwd = _resolve(str(args.cwd))
    prefix = str(args.prefix).strip() or DEFAULT_PREFIX
    if not input_path.is_file():
        raise RuntimeError(f"input dataset not found: {input_path}")
    if not args.mock_decision and not str(args.command).strip():
        raise RuntimeError("provide --command or use --mock-decision for a dry smoke run")

    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = out_dir / f"{prefix}.artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    receipts_path = out_dir / f"{prefix}.receipts.jsonl"

    rows = _load_jsonl(input_path)
    start = max(0, int(args.start_index))
    end = len(rows) if int(args.limit) <= 0 else min(len(rows), start + int(args.limit))
    selected = list(enumerate(rows[start:end], start=start))
    caller = None
    if not args.mock_decision:
        caller = CodexCLICaller(
            command=str(args.command),
            prompt_mode=str(args.prompt_mode),
            timeout_sec=float(args.timeout_sec),
            cwd=cwd,
            artifacts_dir=artifacts_dir,
        )

    receipt_cache = _load_receipt_cache(receipts_path) if args.resume else {}
    run_config_hash = _run_config_hash(args)
    filtered: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    rewrite_queue: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    route_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()

    for line_index, row in selected:
        prompt = _judge_prompt(
            row,
            judge_profile=str(args.judge_profile),
            extra_instruction=str(args.extra_instruction),
        )
        cache_key = (line_index, _row_id(row), _hash_text(prompt), run_config_hash)
        cached = receipt_cache.get(cache_key)
        if cached:
            receipt = dict(cached)
            receipt["reused"] = True
            judge = receipt.get("judge", {}) if isinstance(receipt.get("judge"), dict) else {}
            route = str(receipt.get("route", "review"))
            route_reasons = [str(item) for item in receipt.get("route_reasons", [])]
            corrected_target = _norm_text(receipt.get("corrected_target"))
        else:
            output: CallerOutput | None = None
            parse_error = ""
            if args.mock_decision:
                judge = _mock_judge(str(args.mock_decision), str(args.mock_corrected_target))
            else:
                assert caller is not None
                output = caller.call(prompt=prompt, slug=_slug(line_index, row))
                if output.timed_out:
                    judge = {"decision": "review", "issues": ["caller_timeout"]}
                    route, route_reasons, corrected_target = _error_route(args, "caller_timeout")
                    receipt = _build_receipt(
                        line_index=line_index,
                        row=row,
                        prompt=prompt,
                        output=output,
                        judge=judge,
                        route=route,
                        route_reasons=route_reasons,
                        corrected_target=corrected_target,
                        args=args,
                        parse_error=parse_error,
                    )
                    receipts.append(receipt)
                    route_counts[route] += 1
                    reason_counts.update(route_reasons)
                    if route == "keep":
                        filtered.append(row if not args.include_judge_metadata else _annotate(row, receipt))
                    elif route == "drop":
                        rejected.append(_annotate(row, receipt))
                    else:
                        review.append(_annotate(row, receipt))
                    continue
                if output.returncode not in (0, None):
                    judge = {"decision": "review", "issues": [f"caller_returncode_{output.returncode}"]}
                    route, route_reasons, corrected_target = _error_route(args, f"caller_returncode_{output.returncode}")
                    receipt = _build_receipt(
                        line_index=line_index,
                        row=row,
                        prompt=prompt,
                        output=output,
                        judge=judge,
                        route=route,
                        route_reasons=route_reasons,
                        corrected_target=corrected_target,
                        args=args,
                    )
                    receipts.append(receipt)
                    route_counts[route] += 1
                    reason_counts.update(route_reasons)
                    if route == "keep":
                        filtered.append(row if not args.include_judge_metadata else _annotate(row, receipt))
                    elif route == "drop":
                        rejected.append(_annotate(row, receipt))
                    else:
                        review.append(_annotate(row, receipt))
                    continue
                try:
                    judge = _parse_judge_json(output.stdout)
                except Exception as exc:
                    parse_error = str(exc)
                    judge = {"decision": "review", "issues": ["parse_error"], "parse_error": parse_error}
                    route, route_reasons, corrected_target = _error_route(args, "parse_error")
                    receipt = _build_receipt(
                        line_index=line_index,
                        row=row,
                        prompt=prompt,
                        output=output,
                        judge=judge,
                        route=route,
                        route_reasons=route_reasons,
                        corrected_target=corrected_target,
                        args=args,
                        parse_error=parse_error,
                    )
                    receipts.append(receipt)
                    route_counts[route] += 1
                    reason_counts.update(route_reasons)
                    if route == "keep":
                        filtered.append(row if not args.include_judge_metadata else _annotate(row, receipt))
                    elif route == "drop":
                        rejected.append(_annotate(row, receipt))
                    else:
                        review.append(_annotate(row, receipt))
                    continue
            route, route_reasons, corrected_target = _route_judge(judge=judge, args=args)
            receipt = _build_receipt(
                line_index=line_index,
                row=row,
                prompt=prompt,
                output=output,
                judge=judge,
                route=route,
                route_reasons=route_reasons,
                corrected_target=corrected_target,
                args=args,
                parse_error=parse_error,
            )

        receipts.append(receipt)
        route_counts[route] += 1
        reason_counts.update(route_reasons)
        if corrected_target:
            rewrite_queue.append(_annotate(row, receipt))
        if route == "keep":
            out_row = _apply_rewrite(row, corrected_target) if corrected_target and args.rewrite_mode == "apply" else row
            filtered.append(out_row if not args.include_judge_metadata else _annotate(out_row, receipt))
        elif route == "drop":
            rejected.append(_annotate(row, receipt))
        else:
            review.append(_annotate(row, receipt))

    filtered_path = out_dir / f"{prefix}.filtered.jsonl"
    rejected_path = out_dir / f"{prefix}.rejected.jsonl"
    review_path = out_dir / f"{prefix}.review.jsonl"
    rewrite_path = out_dir / f"{prefix}.rewrite_queue.jsonl"
    summary_json_path = out_dir / f"{prefix}.summary.json"
    summary_md_path = out_dir / f"{prefix}.summary.md"

    _write_jsonl(filtered_path, filtered)
    _write_jsonl(rejected_path, rejected)
    _write_jsonl(review_path, review)
    _write_jsonl(rewrite_path, rewrite_queue)
    _write_jsonl(receipts_path, receipts)

    summary = {
        "generated_utc": _now_utc(),
        "builder": _safe_rel(Path(__file__)),
        "input": _safe_rel(input_path),
        "out_dir": _safe_rel(out_dir),
        "prefix": prefix,
        "command": "mock" if args.mock_decision else str(args.command),
        "prompt_mode": args.prompt_mode,
        "judge_profile": args.judge_profile,
        "extra_instruction": args.extra_instruction,
        "rewrite_mode": args.rewrite_mode,
        "thresholds": {
            "min_adequacy": float(args.min_adequacy),
            "min_literalness": float(args.min_literalness),
            "min_entity_number_preservation": float(args.min_entity_number_preservation),
            "min_confidence": float(args.min_confidence),
        },
        "input_rows": len(rows),
        "start_index": start,
        "processed_rows": len(selected),
        "route_counts": dict(sorted(route_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "outputs": {
            "filtered": _safe_rel(filtered_path),
            "rejected": _safe_rel(rejected_path),
            "review": _safe_rel(review_path),
            "rewrite_queue": _safe_rel(rewrite_path),
            "receipts": _safe_rel(receipts_path),
            "summary_json": _safe_rel(summary_json_path),
            "summary_md": _safe_rel(summary_md_path),
        },
    }
    _write_json(summary_json_path, summary)
    _write_summary_md(summary_md_path, summary)

    print(
        "[cli-judge-filter] "
        f"processed={len(selected)} "
        f"keep={route_counts.get('keep', 0)} "
        f"drop={route_counts.get('drop', 0)} "
        f"review={route_counts.get('review', 0)}"
    )
    print(f"[cli-judge-filter] filtered={_safe_rel(filtered_path)}")
    print(f"[cli-judge-filter] rejected={_safe_rel(rejected_path)}")
    print(f"[cli-judge-filter] review={_safe_rel(review_path)}")
    print(f"[cli-judge-filter] receipts={_safe_rel(receipts_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
