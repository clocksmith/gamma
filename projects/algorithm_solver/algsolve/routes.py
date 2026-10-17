"""The four compared routes.

1. lookup          known-answer lookup; returns a stored solution only when the
                   lookup matches AND the adapted solution passes the public
                   examples; otherwise abstains.
2. model_alone     the control: the model sees the problem only.
3. retrieval       the model also sees the k most similar solved index problems.
4. classify_template  the classifier picks up to two patterns; the model sees
                   their templates (no template when the prediction is unknown).

Routes 2-4 share one budget: the same first-attempt token cap, one repair with
the same token cap, and one wall-clock limit for everything the route does
(classification, retrieval, generation, repair, public-example judging). The
repair sees only public-example failures. Hidden tests are never used here.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from . import validate
from .judge import judge
from .lookup import LookupIndex, adapt_solution, fingerprint
from .model import Generation, Generator, extract_code
from .patterns.catalog import render
from .records import Problem
from .splits import IndexEntry

SYSTEM = "You are an expert competitive programmer. You write correct, efficient Python 3 using only the standard library."
RELATED_INSTRUCTION = "Instruct: Given a programming problem, retrieve solved problems that use a similar algorithm\nQuery: "
STATEMENT_EXCERPT_CHARS = 1200


@dataclass
class Budget:
    first_max_new_tokens: int
    repair_max_new_tokens: int
    repairs: int
    route_wall_seconds: float
    judge_wall_seconds: float
    judge_reserve_seconds: float
    min_repair_seconds: float
    retrieval_k: int

    @classmethod
    def from_contract(cls, contract: dict) -> "Budget":
        b = contract["budgets"]
        return cls(
            first_max_new_tokens=b["first_attempt_max_new_tokens"],
            repair_max_new_tokens=b["repair_max_new_tokens"],
            repairs=b["repairs"],
            route_wall_seconds=b["route_wall_seconds"],
            judge_wall_seconds=b["judge_wall_seconds"],
            judge_reserve_seconds=b["judge_reserve_seconds"],
            min_repair_seconds=b["min_repair_seconds"],
            retrieval_k=b["retrieval_k"],
        )


@dataclass
class RouteResult:
    route: str
    uid: str
    code: str | None
    decision: str = "answered"               # answered | abstain | no_code
    seconds: float = 0.0
    stages: dict[str, float] = field(default_factory=dict)
    attempts: list[dict] = field(default_factory=list)
    budget_exhausted: bool = False
    detail: dict[str, Any] = field(default_factory=dict)
    gpu_peak_bytes: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class Context:
    def __init__(self, *, generator: Generator, embedder, lookup: LookupIndex, thresholds: dict,
                 classifier, entries: list[IndexEntry], budget: Budget) -> None:
        self.generator = generator
        self.embedder = embedder
        self.lookup = lookup
        self.thresholds = thresholds
        self.classifier = classifier
        self.entries = entries
        self.budget = budget
        self.retrievable = [i for i, e in enumerate(entries) if e.references]


# --- prompts -----------------------------------------------------------------

def problem_prompt(problem: Problem) -> str:
    if problem.io_mode == "functional":
        return (
            f"### Problem\n{problem.statement.strip()}\n\n### Starter code\n```python\n{problem.starter_code.rstrip()}\n```\n\n"
            "Return one ```python code block containing the complete `class Solution` with the exact method "
            "signature from the starter code. `List`, `Optional`, `ListNode` and `TreeNode` are predefined. "
            "No explanations, no example usage."
        )
    return (
        f"### Problem\n{problem.statement.strip()}\n\n"
        "Read the input from standard input and write the answer to standard output. Return one ```python "
        "code block with the complete program. No explanations."
    )


def retrieval_block(context: Context, problem: Problem, timings: dict) -> tuple[str, list[str]]:
    started = time.perf_counter()
    vector = context.embedder.encode([problem.query_text()], query=True, instruction=RELATED_INSTRUCTION)[0]
    sims = context.lookup.embeddings[context.retrievable] @ vector
    order = sims.argsort()[::-1][: context.budget.retrieval_k]
    chosen = [context.entries[context.retrievable[i]] for i in order]
    timings["retrieve"] = time.perf_counter() - started
    parts = ["### Related solved problems (different problems; for reference only)"]
    for entry in chosen:
        excerpt = entry.statement.strip()[:STATEMENT_EXCERPT_CHARS]
        parts.append(f"Problem: {entry.title}\n{excerpt}\nSolution:\n```python\n{entry.references[0]['code'].rstrip()}\n```")
    return "\n\n".join(parts), [e.key for e in chosen]


def template_block(context: Context, problem: Problem, timings: dict) -> tuple[str, dict]:
    prediction = context.classifier.predict(problem.statement)
    timings["classify"] = prediction.seconds
    info = {"patterns": prediction.patterns, "top_probabilities": dict(sorted(prediction.probabilities.items(), key=lambda kv: -kv[1])[:4])}
    if prediction.unknown:
        return "", info
    return (
        "### Likely algorithm pattern(s)\n" + render(prediction.patterns)
        + "\n\nAdapt the template to this problem and fill every HOLE; the template's function name and arguments "
          "are placeholders."
    ), info


def describe_failure(problem: Problem, verdict: judge.Verdict) -> str:
    first = verdict.first_failure or {}
    reason = verdict.reason
    if reason == judge.WRONG_ANSWER and "i" in first:
        test = problem.public_tests[first["i"]]
        shown_input = json.dumps(test["args"]) if problem.io_mode == "functional" else test["input"]
        if problem.io_mode == "stdin":
            return (f"Your solution gave a wrong answer on a public example.\nInput:\n{shown_input}\n"
                    f"Expected output:\n{test['expected']}\nYour output:\n{first.get('observed') or ''}")
        return (f"Your solution gave a wrong answer on a public example.\nInput: {shown_input}\n"
                f"Expected: {json.dumps(test['expected'])}\nGot: {json.dumps(first.get('observed'))}")
    if reason in (judge.RUNTIME_ERROR, judge.LOAD_ERROR):
        detail = first.get("error") or first.get("load_error") or ""
        return (f"Your solution raised an error on a public example: {detail} {first.get('detail') or ''}\n"
                f"stderr tail:\n{verdict.stderr_tail[-400:]}")
    if reason == judge.TIMEOUT:
        return "Your solution exceeded the time limit on a public example. Make it faster."
    return f"Your solution failed the public examples ({reason})."


# --- routes ------------------------------------------------------------------

def _public_check(problem: Problem, code: str, wall: float) -> judge.Verdict:
    return validate.judge_problem(problem, code, problem.public_tests, wall_seconds=max(1.0, wall))


def run_lookup(context: Context, problem: Problem) -> RouteResult:
    started = time.perf_counter()
    stages: dict[str, float] = {}
    result = RouteResult(route="lookup", uid=problem.uid, code=None, decision="abstain")
    t = time.perf_counter()
    vector = context.embedder.encode([problem.query_text()], query=True)[0]
    stages["embed"] = time.perf_counter() - t
    t = time.perf_counter()
    match = context.lookup.match(problem.query_text(), vector, context.thresholds)
    stages["match"] = time.perf_counter() - t
    result.detail = {"match_decision": match.decision, "key": match.key, "score": round(match.score, 4),
                     "runner_up": match.runner_up_key, "runner_up_score": round(match.runner_up_score, 4)}
    if match.decision == "match":
        entry = context.entries[context.lookup.by_key[match.key]]
        query_method = fingerprint(problem.query_text()).method or None
        code = adapt_solution(entry.references[0]["code"], entry, query_method) if entry.references else None
        if code is None:
            result.detail["rejected"] = "matched entry has no reference"
        else:
            t = time.perf_counter()
            verdict = _public_check(problem, code, context.budget.judge_wall_seconds)
            stages["public_judge"] = time.perf_counter() - t
            result.attempts.append({"stage": "lookup", "public": verdict.to_dict()})
            if verdict.passed:
                result.code, result.decision = code, "answered"
            else:
                result.detail["rejected"] = f"public examples: {verdict.reason}"
    result.stages = stages
    result.seconds = time.perf_counter() - started
    return result


def run_generative(context: Context, problem: Problem, route: str, *,
                   retrieved_context: tuple[str, list[str]] | None = None) -> RouteResult:
    torch = context.generator.torch  # None for CLI solvers (no local generation)
    if torch is not None:
        torch.cuda.reset_peak_memory_stats()
    budget = context.budget
    started = time.perf_counter()
    deadline = started + budget.route_wall_seconds
    stages: dict[str, float] = {}
    result = RouteResult(route=route, uid=problem.uid, code=None, decision="no_code")
    extra = ""
    if route == "retrieval":
        extra, keys = retrieved_context if retrieved_context is not None else retrieval_block(context, problem, stages)
        result.detail["retrieved"] = keys
    elif route == "classify_template":
        extra, info = template_block(context, problem, stages)
        result.detail["classifier"] = info
    elif route != "model_alone":
        raise ValueError(route)
    user = problem_prompt(problem) if not extra else f"{extra}\n\n{problem_prompt(problem)}"
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]

    def remaining() -> float:
        return deadline - time.perf_counter()

    for attempt in range(1 + budget.repairs):
        if attempt > 0 and remaining() < budget.min_repair_seconds:
            result.detail["repair_skipped"] = f"budget: {remaining():.1f}s left"
            result.budget_exhausted = True
            break
        max_new = budget.first_max_new_tokens if attempt == 0 else budget.repair_max_new_tokens
        gen: Generation = context.generator.generate(
            messages, max_new_tokens=max_new, max_time=remaining() - budget.judge_reserve_seconds
        )
        key = "generate" if attempt == 0 else "repair_generate"
        stages[key] = stages.get(key, 0.0) + gen.seconds
        code = extract_code(gen.text)
        record = {"stage": "first" if attempt == 0 else "repair", "prompt_tokens": gen.prompt_tokens,
                  "new_tokens": gen.new_tokens, "generate_seconds": round(gen.seconds, 3),
                  "stopped_by": gen.stopped_by, "code": code, "meta": gen.meta}
        if gen.stopped_by == "max_time":
            result.budget_exhausted = True
        if not code.strip():
            record["public"] = None
            result.attempts.append(record)
            break
        t = time.perf_counter()
        verdict = _public_check(problem, code, min(budget.judge_wall_seconds, max(remaining(), 1.0)))
        stages["public_judge"] = stages.get("public_judge", 0.0) + time.perf_counter() - t
        record["public"] = verdict.to_dict()
        result.attempts.append(record)
        result.code, result.decision = code, "answered"
        if verdict.passed:
            break
        messages = messages + [
            {"role": "assistant", "content": f"```python\n{code}```"},
            {"role": "user", "content": describe_failure(problem, verdict)
             + "\nFix the solution. Return one complete ```python code block only."},
        ]
    result.stages = stages
    result.seconds = time.perf_counter() - started
    result.gpu_peak_bytes = int(torch.cuda.max_memory_allocated()) if torch is not None else None
    return result


ROUTES = ("lookup", "model_alone", "retrieval", "classify_template")


def run_route(context: Context, problem: Problem, route: str) -> RouteResult:
    if route == "lookup":
        return run_lookup(context, problem)
    return run_generative(context, problem, route)
