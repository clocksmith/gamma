"""Expressibility audit: can a problem be written in the declared composition grammar?

A proposer (claude -p, then codex exec if needed) returns either a composition
(JSON) or a claim that the problem is outside the grammar. A composition is
evidence only after it renders under the grammar and passes the judge.

Labels:
  demonstrated_expressible   a composition rendered and passed the public examples and,
                             where the problem has them, the independent hidden tests
                             (evidence level recorded)
  outside_declared_grammar   the proposer's last answer claims a construct the grammar lacks
                             (category recorded) and no passing composition was found
  unresolved                 neither, within the audit budget

Failure to find a composition does not prove none exists; the headline number
is "demonstrated coverage". Feedback to the proposer: grammar/render errors,
public-example failures, and for hidden tests only pass counts (never inputs).

    python -m algsolve.synth.audit dev       # index development set (vocabulary may still change)
    python -m algsolve.synth.audit heldout   # frozen vocabulary on the 150 held-out problems
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import re
import subprocess
import sys
import time
from pathlib import Path

from .. import splits, validate
from ..cli_solvers import SOLVERS, SolverUnavailable
from ..records import LANE_ROOT, Problem, load_hidden_tests
from . import components, grammar, render, skeletons

VOCAB_FILES = ("grammar.py", "components.py", "skeletons.py", "render.py")
VOCAB_PATH = LANE_ROOT / "contracts" / "synth_vocabulary.json"
AUDIT_RUNS = LANE_ROOT / "runs"
DEV_SIZE = 60
DEV_SEED = 20261018
PROPOSERS = (("claude", 3), ("codex", 2))
CALL_SECONDS = 240.0

CATEGORIES = ("new_primitive", "new_recurrence", "control_structure", "io_format", "size_limit", "other")

EXAMPLES = r'''
Example A (functional, Two Sum):
{"stages": [{"skeleton": "hash_scan", "inputs": ["nums", "target"], "output": "res",
  "holes": {"seq": "nums", "init": "pos = {}\nans = None",
            "query": "ans = [pos[target - x], i] if ans is None and target - x in pos else ans",
            "update": "pos[x] = i if x not in pos else pos[x]", "result": "ans"}}],
 "answer": "res"}

Example B (functional, House Robber):
{"stages": [{"skeleton": "memo", "inputs": ["nums"], "output": "best",
  "holes": {"params": "('i',)", "base_cond": "i >= len(nums)", "base_value": "0",
            "transition": "max(f(i + 1), nums[i] + f(i + 2))", "start": "(0,)"}}],
 "answer": "best"}

Example C (stdin, t test cases, each "a b", print a+b):
{"io": {"mode": "stdin", "cases": "multi", "parse": "a = ni()\nb = ni()", "output": "s"},
 "stages": [{"skeleton": "formula", "inputs": ["a", "b"], "output": "s", "holes": {"value": "a + b"}}]}
'''


def vocabulary_hash() -> str:
    digest = hashlib.sha256()
    base = Path(__file__).parent
    for name in VOCAB_FILES:
        digest.update(name.encode())
        digest.update((base / name).read_bytes())
    return digest.hexdigest()


def grammar_text() -> str:
    return (
        f"Holes hold an expression (max {grammar.MAX_EXPR_NODES} AST nodes) or simple statements (max "
        f"{grammar.MAX_STMTS} statements, {grammar.MAX_STMT_NODES} nodes; assignments, augmented assignments, "
        "expression calls, if, one non-nested for loop, break/continue). No def/class/import/while/try/return in "
        "holes. Comprehensions use one generator. Lambdas are allowed for keys and predicates. Calls allowed: "
        f"{', '.join(sorted(grammar.ALLOWED_CALLS))}, and component functions (c_*). Methods allowed: "
        f"{', '.join(sorted(grammar.ALLOWED_METHODS))}. Available names: inf, Counter, defaultdict, deque. "
        f"At most {render.MAX_STAGES} stages; total hole nodes at most {grammar.MAX_COMPOSITION_NODES}. "
        "A stage's inputs are names in scope (method parameters, parsed variables, earlier stage outputs); "
        "inside a stage only its inputs and the skeleton's names exist."
    )


def build_prompt(problem: Problem) -> str:
    if problem.io_mode == "functional":
        interface = (f"Functional problem. Method `{problem.entry.get('method')}` with parameters "
                     f"{[p[0] for p in problem.params]}. Omit `io` (or use mode functional); give `answer`.")
    else:
        interface = ("Standard input/output problem. Use io mode stdin with `parse` statements (ni, nf, nxt, nl(k), "
                     "lines) and an `output` expression (a string or value printed per case).")
    return f"""You are auditing whether a programming problem can be solved inside a fixed composition grammar.
You may NOT write free-form code: only fill skeleton holes.

GRAMMAR
{grammar_text()}

SKELETONS
{skeletons.catalog_text()}

COMPONENTS (callable inside holes)
{components.catalog_text()}

EXAMPLES
{EXAMPLES}

PROBLEM
{problem.statement.strip()}

{('Starter code:' + chr(10) + problem.starter_code.strip()) if problem.starter_code.strip() else ''}

{interface}

Answer with exactly one JSON object and nothing else:
- a composition (as in the examples), if the problem can be solved correctly and efficiently within the grammar; or
- {{"verdict": "outside_grammar", "category": one of {list(CATEGORIES)}, "reason": "<what is missing>"}}
"""


def parse_answer(text: str) -> dict | None:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.S)
    if fence:
        text = fence.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def check_composition(problem: Problem, composition: dict) -> dict:
    params = [p[0] for p in problem.params]
    try:
        rendered = render.render(composition, method=problem.entry.get("method"), params=params)
    except (grammar.GrammarError, SyntaxError, ValueError, KeyError, TypeError) as exc:
        return {"stage": "render", "ok": False, "error": f"{type(exc).__name__}: {exc}"[:400]}
    public = validate.judge_problem(problem, rendered.source, problem.public_tests) if problem.public_tests else None
    if public is not None and not public.passed:
        return {"stage": "public", "ok": False, "public": public.to_dict(), "rendered": _rendered_info(rendered)}
    hidden_tests = load_hidden_tests(problem)
    hidden = validate.judge_problem(problem, rendered.source, hidden_tests, wall_seconds=120.0) if hidden_tests else None
    ok = hidden.passed if hidden is not None else public is not None
    evidence = ("independent_tests_passed" if hidden is not None and hidden.passed
                and problem.evidence_ceiling == "independent_tests_passed" else "example_passed" if ok else None)
    return {"stage": "hidden", "ok": ok, "evidence": evidence,
            "public": public.to_dict() if public else None,
            "hidden": {k: hidden.to_dict()[k] for k in ("passed", "reason", "tests_total", "tests_passed")} if hidden else None,
            "rendered": _rendered_info(rendered)}


def _rendered_info(rendered: render.Rendered) -> dict:
    return {"nodes": rendered.nodes, "families": rendered.families, "skeletons": rendered.skeletons,
            "components": rendered.components, "source_sha256": hashlib.sha256(rendered.source.encode()).hexdigest()}


def feedback(problem: Problem, result: dict) -> str:
    if result["stage"] == "render":
        return f"The composition was rejected: {result['error']}"
    if result["stage"] == "public":
        public = result["public"]
        first = public.get("first_failure") or {}
        detail = json.dumps({k: first.get(k) for k in ("i", "reason", "expected", "observed", "error", "detail") if first.get(k) is not None})
        return f"The rendered program failed a public example ({public.get('reason')}): {detail[:600]}"
    hidden = result.get("hidden") or {}
    return (f"The rendered program passed the public examples but failed hidden tests "
            f"({hidden.get('tests_passed')}/{hidden.get('tests_total')} passed, reason {hidden.get('reason')}).")


def audit_problem(problem: Problem, proposers) -> dict:
    record = {"uid": problem.uid, "source": problem.source, "io_mode": problem.io_mode, "attempts": []}
    last_claim = None
    for name, budget in proposers:
        generator = SOLVERS[name]()
        messages = [{"role": "system", "content": "Answer with one JSON object only."},
                    {"role": "user", "content": build_prompt(problem)}]
        for attempt in range(budget):
            started = time.perf_counter()
            gen = generator.generate(messages, max_new_tokens=4096, max_time=CALL_SECONDS)
            answer = parse_answer(gen.text)
            entry = {"proposer": name, "attempt": attempt, "seconds": round(time.perf_counter() - started, 2),
                     "stopped_by": gen.stopped_by, "tool_items": (gen.meta or {}).get("tool_items")}
            if answer is None:
                entry["outcome"] = "unparseable"
                record["attempts"].append(entry)
                messages = messages + [{"role": "assistant", "content": gen.text[:2000]},
                                       {"role": "user", "content": "That was not one JSON object. Answer with one JSON object only."}]
                continue
            if answer.get("verdict") == "outside_grammar":
                entry.update(outcome="claims_outside", category=answer.get("category"), reason=str(answer.get("reason"))[:400])
                record["attempts"].append(entry)
                last_claim = entry
                break
            result = check_composition(problem, answer)
            entry.update(outcome="passed" if result["ok"] else f"failed_{result['stage']}", check=result)
            entry["composition"] = answer
            record["attempts"].append(entry)
            if result["ok"]:
                record.update(label="demonstrated_expressible", evidence=result["evidence"],
                              rendered=result["rendered"], composition=answer, proposer=name)
                return record
            messages = messages + [{"role": "assistant", "content": json.dumps(answer)},
                                   {"role": "user", "content": feedback(problem, result) + " Revise: answer with one JSON object."}]
    if last_claim is not None and not any(a.get("outcome") == "passed" for a in record["attempts"]):
        record.update(label="outside_declared_grammar", category=last_claim.get("category"), reason=last_claim.get("reason"))
    else:
        record["label"] = "unresolved"
    return record


def dev_problems(problems: dict[str, Problem]) -> list[Problem]:
    """Index problems with validated tests, outside every evaluation and recognition query, stratified by tag."""
    manifest = splits.load_manifest()
    entries = splits.read_index_entries()
    used = {q.get("target") for q in manifest["recognition"] + manifest["recognition_dev"]}
    from ..patterns.catalog import patterns_for_tags
    pool = [e for e in entries if e.judge_uid and e.key not in used]
    by_pattern = collections.defaultdict(list)
    for e in pool:
        pats = patterns_for_tags(e.tags) or ["none"]
        by_pattern[pats[0]].append(e)
    rng = random.Random(DEV_SEED)
    chosen = []
    names = sorted(by_pattern)
    while len(chosen) < DEV_SIZE:
        for name in names:
            bucket = sorted(by_pattern[name], key=lambda e: e.key)
            remaining = [e for e in bucket if e not in chosen]
            if remaining and len(chosen) < DEV_SIZE:
                chosen.append(rng.choice(remaining))
    return [problems[e.judge_uid] for e in chosen]


def heldout_problems(problems: dict[str, Problem]) -> list[Problem]:
    manifest = splits.load_manifest()
    uids = manifest["solving"]["lcd"] + manifest["solving"]["lcb"] + manifest["solving"]["cf"]
    return [problems[u] for u in uids]


def require_frozen() -> str:
    if not VOCAB_PATH.exists():
        raise SystemExit("vocabulary is not frozen; run `freeze` after the development audit")
    frozen = json.loads(VOCAB_PATH.read_text())
    digest = vocabulary_hash()
    if frozen["sha256"] != digest:
        raise SystemExit(f"vocabulary changed since freezing ({digest[:12]} != {frozen['sha256'][:12]})")
    status = subprocess.run(["git", "status", "--porcelain", "--", "algsolve/synth", "contracts/synth_vocabulary.json"],
                            cwd=LANE_ROOT, capture_output=True, text=True).stdout.strip()
    if status:
        raise SystemExit("vocabulary files have uncommitted changes")
    return digest


def freeze() -> dict:
    info = {
        "sha256": vocabulary_hash(),
        "files": [f"algsolve/synth/{n}" for n in VOCAB_FILES],
        "skeletons": {k: v["family"] for k, v in skeletons.SKELETONS.items()},
        "components": sorted(components.COMPONENTS),
        "limits": {"max_expr_nodes": grammar.MAX_EXPR_NODES, "max_stmts": grammar.MAX_STMTS,
                   "max_stmt_nodes": grammar.MAX_STMT_NODES, "max_composition_nodes": grammar.MAX_COMPOSITION_NODES,
                   "max_stages": render.MAX_STAGES},
        "built_from": "index problems and the 13 route templates only; held-out solving problems not consulted",
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    VOCAB_PATH.write_text(json.dumps(info, indent=1) + "\n")
    return info


def run_audit(name: str, selected: list[Problem], vocab: str) -> Path:
    out_dir = AUDIT_RUNS / name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "audit.jsonl"
    done = set()
    if out_path.exists():
        done = {json.loads(l)["uid"] for l in out_path.read_text().splitlines() if l.strip()}
    with out_path.open("a", encoding="utf-8") as out:
        for n, problem in enumerate(selected):
            if problem.uid in done:
                continue
            try:
                record = audit_problem(problem, PROPOSERS)
            except SolverUnavailable as exc:
                print(f"[audit] proposer unavailable, stopping for resume: {exc}", flush=True)
                break
            record["vocabulary_sha256"] = vocab
            out.write(json.dumps(record) + "\n")
            out.flush()
            print(f"[audit] {n + 1}/{len(selected)} {problem.uid} {record['label']}", flush=True)
    summarize(out_dir)
    return out_dir


def summarize(out_dir: Path) -> dict:
    rows = [json.loads(l) for l in (out_dir / "audit.jsonl").read_text().splitlines() if l.strip()]
    labels = collections.Counter(r["label"] for r in rows)
    by_source = collections.defaultdict(collections.Counter)
    for r in rows:
        by_source[r["source"]][r["label"]] += 1
    demonstrated = [r for r in rows if r["label"] == "demonstrated_expressible"]
    generic = {"generic"}
    summary = {
        "problems": len(rows),
        "labels": dict(labels),
        "demonstrated_coverage": round(len(demonstrated) / len(rows), 4) if rows else None,
        "demonstrated_by_evidence": dict(collections.Counter(r.get("evidence") for r in demonstrated)),
        "demonstrated_using_only_generic_skeletons": sum(1 for r in demonstrated if set(r["rendered"]["families"]) <= generic),
        "demonstrated_families": dict(collections.Counter(f for r in demonstrated for f in r["rendered"]["families"])),
        "demonstrated_hole_nodes": sorted(r["rendered"]["nodes"] for r in demonstrated),
        "outside_categories": dict(collections.Counter(r.get("category") for r in rows if r["label"] == "outside_declared_grammar")),
        "by_source": {k: dict(v) for k, v in by_source.items()},
        "proposer_of_success": dict(collections.Counter(r.get("proposer") for r in demonstrated)),
        "attempts_with_tool_items": sum(1 for r in rows for a in r["attempts"] if (a.get("tool_items") or 0) > 0),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("dev", "freeze", "heldout", "summary"))
    parser.add_argument("--name", default=None)
    args = parser.parse_args(argv)
    problems = splits.load_all()
    if args.action == "freeze":
        print(json.dumps(freeze(), indent=1))
        return 0
    if args.action == "summary":
        print(json.dumps(summarize(AUDIT_RUNS / args.name), indent=1))
        return 0
    if args.action == "dev":
        out = run_audit(args.name or f"audit-dev-{vocabulary_hash()[:8]}", dev_problems(problems), vocabulary_hash())
    else:
        vocab = require_frozen()
        out = run_audit(args.name or f"audit-heldout-{vocab[:8]}", heldout_problems(problems), vocab)
    print(json.dumps(summarize(out), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
