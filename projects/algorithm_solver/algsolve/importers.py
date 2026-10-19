"""Import the fetched sources into normalized Problem records.

Writes data/derived/problems.jsonl (one record per problem, all sources) and
data/derived/tests/<uid>.json (hidden tests). Dropped tests and dropped
problems are counted in each record's import_notes and in import_report.json.

LiveCodeBench hidden tests are pickled; they are decoded only inside the
sandbox (see decode_lcb_private) and come back to the host as JSON.
"""

from __future__ import annotations

import ast
import collections
import html
import json
import re
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from . import values
from .judge import sandbox
from .records import DERIVED, EXAMPLE, INDEPENDENT, RAW, Problem, write_hidden_tests, write_problems

LCD_DIR = RAW / "newfacade__LeetCodeDataset"
LCB_FILE = RAW / "livecodebench__code_generation_lite" / "test6.jsonl"
CF_FILE = RAW / "open-r1__codeforces" / "verifiable" / "test-00000-of-00001.parquet"
DOOCS_DIR = RAW / "doocs__leetcode" / "solution"

LCD_LICENSE = "LeetCodeDataset: apache-2.0 (HF) / MIT (GitHub); problem text from LeetCode"
LCB_LICENSE = "LiveCodeBench code_generation_lite: card 'cc' / loader MIT"
CF_LICENSE = "open-r1/codeforces: cc-by-4.0 (YAML) / ODC-By 4.0 (card)"
DOOCS_LICENSE = "doocs/leetcode CC-BY-SA-4.0; commercial reprints need author authorization; research use only"


# --- statement examples ------------------------------------------------------

_EXAMPLE_RE = re.compile(
    r"Input:?\s*(?P<input>.+?)\s*\n\s*Output:?\s*(?P<output>.+?)\s*(?:\n|$)",
    re.S,
)


def statement_examples(statement: str, params: list[tuple[str, str]], ret_annotation: str) -> tuple[list[dict], int]:
    tests = []
    matches = list(_EXAMPLE_RE.finditer(statement))
    # A trailing/incomplete explicit Input block has no regex match. Count it
    # as dropped so recovery cannot approve only the other examples. Labels
    # inside a captured literal are already part of that example, not new ones.
    labels = re.finditer(r"(?m)^[ \t]*(?P<label>Input)(?=:|[ \t]|$)", statement)
    dropped = sum(not any(match.start() <= label.start('label') < match.end()
                          for match in matches) for label in labels)
    for match in matches:
        # Some upstream statements have a literal backslash-r at line endings.
        # Preserve whitespace/escapes inside quoted values; never unescape the
        # whole statement or collapse runs of spaces in string arguments.
        raw_in = re.sub(r"\\r(?=\r?\n|$)", "", match.group("input")).strip()
        raw_out = re.sub(r"\\r(?=\r?\n|$)", "", match.group("output")).strip()
        try:
            args, kwargs = values.parse_call_arguments(raw_in)
            ordered = values.order_arguments(params, args, kwargs)
            ordered = [values.wrap_for_annotation(v, ann) for v, (_, ann) in zip(ordered, params)]
            expected = values.wrap_for_annotation(values.parse_value(raw_out), ret_annotation)
        except (values.Unsupported, AssertionError):
            dropped += 1
            continue
        tests.append({"args": ordered, "expected": values.canonicalize(expected), "compare": "return"})
    return tests, dropped


# --- LeetCodeDataset ---------------------------------------------------------

def _lcd_assert(stmt: ast.stmt) -> tuple[ast.Call, ast.AST]:
    if not isinstance(stmt, ast.Assert):
        raise values.Unsupported("not an assert")
    test = stmt.test
    if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
        call, expected = test.left, test.comparators[0]
    elif (
        isinstance(test, ast.Call)
        and isinstance(test.func, ast.Name)
        and test.func.id in ("is_same_list", "is_same_tree")
        and len(test.args) == 2
    ):
        call, expected = test.args
    else:
        raise values.Unsupported("assert form")
    if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "candidate"):
        raise values.Unsupported("assert does not call candidate")
    return call, expected


def lcd_hidden_tests(test_source: str, params: list[tuple[str, str]]) -> tuple[list[dict], int]:
    try:
        module = ast.parse(test_source)
    except SyntaxError:
        return [], -1
    check = next((n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "check"), None)
    if check is None:
        return [], -1
    tests, dropped = [], 0
    for stmt in check.body:
        try:
            call, expected_node = _lcd_assert(stmt)
            args = [values.evaluate(a) for a in call.args]
            kwargs = {k.arg: values.evaluate(k.value) for k in call.keywords if k.arg}
            ordered = values.order_arguments(params, args, kwargs)
            expected = values.evaluate(expected_node)
        except values.Unsupported:
            dropped += 1
            continue
        tests.append({"args": ordered, "expected": values.canonicalize(expected), "compare": "return"})
    return tests, dropped


def import_lcd() -> list[Problem]:
    problems = []
    for split in ("train", "test"):
        for line in (LCD_DIR / f"LeetCodeDataset-{split}.jsonl").open(encoding="utf-8"):
            row = json.loads(line)
            method = row["entry_point"].split(".", 1)[1]
            problem = Problem(
                uid=f"lcd:{row['question_id']}",
                source="lcd",
                source_id=str(row["question_id"]),
                title=row["task_id"].replace("-", " "),
                slug=row["task_id"],
                statement=row["problem_description"].strip(),
                io_mode="functional",
                starter_code=row["starter_code"],
                entry={"class": "Solution", "method": method},
                date=row.get("estimated_date", ""),
                difficulty=row.get("difficulty", ""),
                tags=list(row.get("tags") or []),
                license=LCD_LICENSE,
                attribution=f"https://leetcode.com/problems/{row['task_id']}/ via newfacade/LeetCodeDataset",
                evidence_ceiling=INDEPENDENT,
                reference_solutions=[row["completion"]],
                import_notes={"lcd_split": split},
            )
            try:
                params = values.signature(row["starter_code"], method)
            except values.Unsupported as exc:
                problem.import_notes["unusable"] = f"signature: {exc}"
                problems.append(problem)
                continue
            problem.params = [list(p) for p in params]
            if values.return_annotation(row["starter_code"], method) == "None":
                problem.import_notes["unusable"] = "in-place problem; dataset asserts only check the None return"
                problems.append(problem)
                continue
            hidden, dropped = lcd_hidden_tests(row["test"], params)
            public, public_dropped = statement_examples(
                problem.statement, params, values.return_annotation(row["starter_code"], method)
            )
            problem.public_tests = public
            problem.import_notes.update(
                hidden_tests=len(hidden), hidden_dropped=dropped,
                public_tests=len(public), public_dropped=public_dropped,
            )
            if not hidden:
                problem.import_notes["unusable"] = "no parseable hidden tests"
            write_hidden_tests(problem, hidden)
            problems.append(problem)
    return problems


# --- LiveCodeBench -----------------------------------------------------------

DECODER = r'''
import base64, json, pickle, sys, zlib
blob = open("/task/blob.txt", "rb").read()
value = pickle.loads(zlib.decompress(base64.b64decode(blob)))
if isinstance(value, bytes):
    value = value.decode("utf-8")
if not isinstance(value, str):
    raise SystemExit("decoded payload is not a JSON string")
tests = json.loads(value)
if not isinstance(tests, list):
    raise SystemExit("decoded tests are not a list")
sys.stdout.write(json.dumps(tests))
'''


def decode_lcb_private(blob: str) -> list[dict]:
    """base64 -> zlib -> pickle -> JSON, decoded inside the sandbox."""
    result = sandbox.run(
        [sandbox.PYTHON, "-I", "-S", "decoder.py"],
        files={"decoder.py": DECODER, "blob.txt": blob},
        limits=sandbox.Limits(
            cpu_seconds=120,
            wall_seconds=180.0,
            memory_bytes=8 * 1024**3,
            max_file_bytes=1,
            max_output_bytes=2 * 1024**3,
        ),
    )
    if not result.ok:
        raise RuntimeError(
            f"sandboxed decode failed: exit={result.exit_code} timed_out={result.timed_out} "
            f"stderr={result.stderr[-300:]!r}"
        )
    tests = json.loads(result.stdout)
    for test in tests:
        if not (isinstance(test, dict) and isinstance(test.get("input"), str) and isinstance(test.get("output"), str)):
            raise RuntimeError("decoded test has unexpected shape")
    return tests


def _lcb_functional(test: dict, params: list[tuple[str, str]]) -> dict:
    args = [json.loads(line) for line in test["input"].split("\n") if line.strip()]
    if len(args) != len(params):
        raise values.Unsupported("argument count mismatch")
    return {"args": args, "expected": json.loads(test["output"]), "compare": "return"}


def import_lcb(decode_private_for: set[str] | None = None) -> list[Problem]:
    """decode_private_for: uids whose hidden tests to decode (sampled problems)."""
    problems = []
    for line in LCB_FILE.open(encoding="utf-8"):
        row = json.loads(line)
        functional = row["platform"] == "leetcode"
        uid = f"lcb:{row['question_id']}"
        metadata = json.loads(row["metadata"] or "{}")
        problem = Problem(
            uid=uid,
            source="lcb",
            source_id=row["question_id"],
            title=row["question_title"],
            slug=row["question_title"] if functional else "",
            statement=row["question_content"].strip(),
            io_mode="functional" if functional else "stdin",
            starter_code=row["starter_code"] or "",
            date=row["contest_date"][:10],
            difficulty=row["difficulty"],
            license=LCB_LICENSE,
            attribution=f"LiveCodeBench v6 ({row['platform']} {row['contest_id']})",
            evidence_ceiling=INDEPENDENT,
            import_notes={"platform": row["platform"], "contest_id": row["contest_id"]},
        )
        public_raw = json.loads(row["public_test_cases"])
        try:
            if functional:
                method = metadata["func_name"]
                problem.entry = {"class": "Solution", "method": method}
                params = values.signature(problem.starter_code, method)
                problem.params = [list(p) for p in params]
                problem.public_tests = [_lcb_functional(t, params) for t in public_raw]
            else:
                problem.public_tests = [{"input": t["input"], "expected": t["output"]} for t in public_raw]
        except (values.Unsupported, KeyError, json.JSONDecodeError) as exc:
            problem.import_notes["unusable"] = f"public tests: {exc}"
        if decode_private_for is not None and uid in decode_private_for and "unusable" not in problem.import_notes:
            private = decode_lcb_private(row["private_test_cases"])
            if functional:
                hidden = [_lcb_functional(t, params) for t in private]
            else:
                hidden = [{"input": t["input"], "expected": t["output"]} for t in private]
            hidden = problem.public_tests + hidden
            problem.import_notes.update(hidden_tests=len(hidden), private_decoded=len(private))
            write_hidden_tests(problem, hidden)
        problems.append(problem)
    return problems


# --- Codeforces --------------------------------------------------------------

def _cf_text(text: str | None) -> str:
    return (text or "").replace("$$$", "$").strip()


def import_cf() -> list[Problem]:
    import pyarrow.parquet as pq

    problems = []
    for row in pq.read_table(CF_FILE).to_pylist():
        examples = row.get("examples") or []
        parts = [
            f"{row['title']}",
            f"Time limit: {row['time_limit']} seconds. Memory limit: {row['memory_limit']} MB.",
            _cf_text(row["description"]),
            "Input\n" + _cf_text(row["input_format"]),
            "Output\n" + _cf_text(row["output_format"]),
        ]
        for i, ex in enumerate(examples, 1):
            parts.append(f"Example {i}\nInput:\n{ex['input']}\nOutput:\n{ex['output']}")
        if row.get("note"):
            parts.append("Note\n" + _cf_text(row["note"]))
        complete = bool(row["official_tests_complete"])
        problem = Problem(
            uid=f"cf:{row['id']}",
            source="cf",
            source_id=row["id"],
            title=row["title"],
            slug="",
            statement="\n\n".join(parts),
            io_mode="stdin",
            date=str(row.get("contest_start_year") or ""),
            difficulty=str(row.get("rating") or ""),
            tags=list(row.get("tags") or []),
            license=CF_LICENSE,
            attribution=f"https://codeforces.com/contest/{row['contest_id']}/problem/{row['index']}",
            evidence_ceiling=INDEPENDENT if complete else EXAMPLE,
            cpu_seconds=float(row["time_limit"] or 2.0),
            memory_bytes=int(float(row["memory_limit"] or 256) * 1024 * 1024),
            checker=row.get("generated_checker") or None,
            public_tests=[{"input": ex["input"], "expected": ex["output"]} for ex in examples],
            import_notes={
                "official_tests_complete": complete,
                "testset_size": row.get("testset_size"),
                "interaction": bool(row.get("interaction_format")),
                "input_mode": row.get("input_mode"),
            },
        )
        official = [
            {"input": t["input"].replace("\r\n", "\n"), "expected": t["output"].replace("\r\n", "\n")}
            for t in row.get("official_tests") or []
        ]
        if row.get("interaction_format") or row.get("input_mode") != "stdio" or not row.get("executable", True):
            problem.import_notes["unusable"] = "interactive, file I/O, or not executable"
        problem.import_notes["hidden_tests"] = len(official)
        write_hidden_tests(problem, official)
        problems.append(problem)
    return problems


# --- Doocs -------------------------------------------------------------------

class _HtmlText(HTMLParser):
    BLOCK = {"p", "div", "pre", "li", "ul", "ol", "br", "h1", "h2", "h3", "h4", "tr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCK:
            self.parts.append("\n")
        if tag == "sup":
            self.parts.append("^")
        if tag == "li":
            self.parts.append("- ")

    def handle_endtag(self, tag):
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def html_to_text(markup: str) -> str:
    parser = _HtmlText()
    parser.feed(markup or "")
    text = html.unescape("".join(parser.parts)).replace("\xa0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _as_list(field: Any) -> list:
    if isinstance(field, list):
        return field
    if not field:
        return []
    try:
        value = json.loads(field)
    except (json.JSONDecodeError, TypeError):
        try:
            value = ast.literal_eval(field)
        except (ValueError, SyntaxError):
            return []
    return value if isinstance(value, list) else []


def _python_snippet(snippets_field: Any) -> str:
    snippets = _as_list(snippets_field)
    for snippet in snippets:
        if snippet.get("langSlug") in ("python3", "python"):
            return snippet.get("code", "")
    return ""


def import_doocs() -> list[Problem]:
    rows = json.loads((DOOCS_DIR / "result.json").read_text(encoding="utf-8"))
    problems = []
    for row in rows:
        relative = row["relative_path_en"].lstrip("/").removeprefix("solution/")
        folder = DOOCS_DIR / Path(urllib.parse.unquote(relative)).parent
        solution_file = folder / "Solution.py"
        starter = _python_snippet(row.get("code_snippets", ""))
        method = ""
        match = re.search(r"def (\w+)\(self", starter)
        if match:
            method = match.group(1)
        tags = _as_list(row.get("tags_en"))
        problem = Problem(
            uid=f"doocs:{row['frontend_question_id']}",
            source="doocs",
            source_id=row["frontend_question_id"],
            title=row["title_en"],
            slug=row["question_title_slug"],
            statement=html_to_text(row.get("content_en") or ""),
            io_mode="functional",
            starter_code=starter,
            entry={"class": "Solution", "method": method} if method else {},
            difficulty=row.get("difficulty_en", ""),
            tags=list(tags),
            license=DOOCS_LICENSE,
            attribution=row.get("url_en", ""),
            evidence_ceiling=EXAMPLE,
            reference_solutions=[solution_file.read_text(encoding="utf-8")] if solution_file.exists() else [],
            import_notes={"paid_only": row.get("paid_only"), "category": row.get("category")},
        )
        if method:
            try:
                params = values.signature(starter, method)
                problem.params = [list(p) for p in params]
                problem.public_tests, dropped = statement_examples(
                    problem.statement, params, values.return_annotation(starter, method)
                )
                problem.import_notes["public_dropped"] = dropped
            except values.Unsupported as exc:
                problem.import_notes["signature"] = str(exc)
        if not problem.statement or str(row.get("paid_only")) == "True":
            problem.import_notes["unusable"] = "no statement or paid-only"
        problems.append(problem)
    return problems


def run(decode_lcb_for: set[str] | None = None) -> dict[str, Any]:
    DERIVED.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {}
    everything: list[Problem] = []
    for name, importer in (("lcd", import_lcd), ("cf", import_cf), ("doocs", import_doocs)):
        items = importer()
        everything.extend(items)
        report[name] = _summary(items)
    lcb = import_lcb(decode_lcb_for)
    everything.extend(lcb)
    report["lcb"] = _summary(lcb)
    write_problems(DERIVED / "problems.jsonl", everything)
    (DERIVED / "import_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def _summary(items: list[Problem]) -> dict[str, Any]:
    unusable = collections.Counter(p.import_notes.get("unusable", "usable") for p in items)
    return {
        "problems": len(items),
        "status": dict(unusable),
        "with_reference": sum(1 for p in items if p.reference_solutions),
        "evidence_ceiling": dict(collections.Counter(p.evidence_ceiling for p in items)),
        "hidden_dropped_total": sum(p.import_notes.get("hidden_dropped", 0) or 0 for p in items),
        "public_tests_total": sum(len(p.public_tests) for p in items),
    }


def load_lcb_private_into(problems_path: Path, uids: set[str]) -> dict[str, int]:
    """Decode hidden tests for the frozen LCB sample and update records in place."""
    lcb = {p.uid: p for p in import_lcb(uids)}
    from .records import read_problems
    updated, counts = [], {}
    for problem in read_problems(problems_path):
        if problem.uid in uids and problem.uid in lcb:
            problem = lcb[problem.uid]
            counts[problem.uid] = problem.import_notes.get("hidden_tests", 0)
        updated.append(problem)
    write_problems(problems_path, updated)
    return counts
