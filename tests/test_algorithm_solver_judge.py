"""Fail-closed tests for the algorithm_solver sandbox and judge.

Every adversarial candidate here must end in a failing verdict (or, for the
isolation probes, prove the boundary held) before judge results are trusted.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

import pytest

_LANE = Path(__file__).resolve().parents[1] / "projects" / "algorithm_solver"
if str(_LANE) not in sys.path:
    sys.path.insert(0, str(_LANE))

from algsolve.judge import judge, sandbox  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (Path(sandbox.BWRAP).exists() and Path(sandbox.PRLIMIT).exists()),
    reason="bubblewrap/prlimit not installed",
)

TWO_SUM = """
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i
"""
ENTRY = {"class": "Solution", "method": "twoSum"}
TESTS = [
    judge.FunctionalTest(args=[[2, 7, 11, 15], 9], expected=[0, 1]),
    judge.FunctionalTest(args=[[3, 2, 4], 6], expected=[1, 2]),
    judge.FunctionalTest(args=[[3, 3], 6], expected=[0, 1]),
]


def _solution(body: str) -> str:
    return "class Solution:\n    def twoSum(self, nums, target):\n" + "".join(
        "        " + line + "\n" for line in body.strip().splitlines()
    )


def _fast(**kw):
    return dict(per_test_cpu_seconds=1.0, wall_seconds=8.0, **kw)


def test_correct_solution_passes():
    verdict = judge.judge_functional(TWO_SUM, ENTRY, TESTS, **_fast())
    assert verdict.passed, verdict
    assert verdict.tests_passed == 3


def test_zero_tests_fail_closed():
    verdict = judge.judge_functional(TWO_SUM, ENTRY, [], **_fast())
    assert not verdict.passed and verdict.reason == judge.NO_TESTS
    verdict = judge.judge_stdin("print(1)", [], **_fast())
    assert not verdict.passed and verdict.reason == judge.NO_TESTS


def test_wrong_answer_fails():
    verdict = judge.judge_functional(_solution("return [0, 1]"), ENTRY, TESTS, **_fast())
    assert not verdict.passed and verdict.reason == judge.WRONG_ANSWER
    assert verdict.tests_passed == 2


def test_forged_records_on_saved_stdout_fail():
    # Write fabricated per-test records and a completion marker to the real
    # stdout fd, then exit before the harness can write its own records.
    forged = """
import os, json
for i in range(3):
    os.write(3, (json.dumps({"i": i, "result": [0, 1]}) + "\\n").encode())
os.write(3, b'{"done": 3}\\n')
os._exit(0)
"""
    verdict = judge.judge_functional(forged, ENTRY, TESTS, **_fast())
    assert not verdict.passed, verdict


def test_forged_duplicate_records_fail():
    forged = TWO_SUM + """
import os, json
os.write(3, (json.dumps({"i": 0, "result": [0, 1]}) + "\\n").encode())
"""
    verdict = judge.judge_functional(forged, ENTRY, TESTS, **_fast())
    assert not verdict.passed and verdict.reason == judge.DUPLICATE_RESULT


def test_printed_verdict_text_is_ignored():
    forged = 'print("PASSED all tests"); print(\'{"passed": true}\')\n' + _solution("return []")
    verdict = judge.judge_functional(forged, ENTRY, TESTS, **_fast())
    assert not verdict.passed and verdict.reason == judge.WRONG_ANSWER


def test_expected_values_are_not_in_the_sandbox(monkeypatch):
    sentinel = 918273645
    sent: list[dict] = []
    real = sandbox.run_python

    def capture(name, *, files, stdin=b"", limits=sandbox.Limits()):
        sent.append({"files": files, "stdin": stdin})
        return real(name, files=files, stdin=stdin, limits=limits)

    monkeypatch.setattr(sandbox, "run_python", capture)
    judge.judge_functional(TWO_SUM, ENTRY, [judge.FunctionalTest(args=[[1, 2], 3], expected=[sentinel])], **_fast())
    judge.judge_stdin("print(input())", [judge.StdinTest("1\n", str(sentinel))], **_fast())
    assert len(sent) == 2
    for call in sent:
        blobs = [v.encode() if isinstance(v, str) else v for v in call["files"].values()] + [call["stdin"]]
        assert all(str(sentinel).encode() not in blob for blob in blobs)


def test_early_exit_fails():
    for early in ("import sys\nsys.exit(0)\n", "import os\nos._exit(0)\n"):
        verdict = judge.judge_functional(early + TWO_SUM, ENTRY, TESTS, **_fast())
        assert not verdict.passed, (early, verdict)
        assert verdict.reason in (judge.LOAD_ERROR, judge.MISSING_RESULT)


def test_exit_after_partial_results_fails():
    partial = _solution("""
import os
if len(nums) == 3:
    os._exit(0)
return [0, 1]
""")
    verdict = judge.judge_functional(partial, ENTRY, TESTS, **_fast())
    assert not verdict.passed and verdict.reason == judge.MISSING_RESULT


def test_cpu_hang_times_out():
    verdict = judge.judge_functional(_solution("while True:\n    pass"), ENTRY, TESTS[:1], **_fast())
    assert not verdict.passed and verdict.reason == judge.TIMEOUT


def test_sleeping_hang_hits_wall_limit():
    verdict = judge.judge_functional(
        _solution("import time\ntime.sleep(60)"), ENTRY, TESTS[:1], per_test_cpu_seconds=1.0, wall_seconds=3.0
    )
    assert not verdict.passed and verdict.reason == judge.TIMEOUT
    assert verdict.wall_seconds < 10


def test_excessive_output_fails():
    flood = _solution("import sys\nwhile True:\n    sys.stderr.write('x' * 65536)")
    verdict = judge.judge_functional(flood, ENTRY, TESTS[:1], **_fast())
    assert not verdict.passed and verdict.reason in (judge.OUTPUT_LIMIT, judge.TIMEOUT)
    assert len(verdict.stderr_tail) <= 600


def test_memory_limit_fails():
    hog = _solution("block = bytearray(2 * 1024 * 1024 * 1024)\nreturn [0, 1]")
    verdict = judge.judge_functional(hog, ENTRY, TESTS[:1], **_fast())
    assert not verdict.passed and verdict.reason == judge.RUNTIME_ERROR


def _processes_with(marker: str) -> list[int]:
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        if marker.encode() in cmdline and entry.name != str(os.getpid()):
            found.append(int(entry.name))
    return found


def test_child_processes_do_not_outlive_the_judge():
    marker = "algsolve-orphan-probe-7f3a"
    spawner = _solution(f"""
import subprocess
subprocess.Popen(['/usr/bin/python3', '-c', 'import time; time.sleep(120)', '{marker}'],
                 start_new_session=True)
return [0, 1]
""")
    judge.judge_functional(spawner, ENTRY, TESTS[:1], **_fast())
    assert _processes_with(marker) == []


def test_fork_bomb_is_contained():
    bomb = _solution("""
import os
while True:
    try:
        os.fork()
    except OSError:
        pass
""")
    verdict = judge.judge_functional(bomb, ENTRY, TESTS[:1], per_test_cpu_seconds=1.0, wall_seconds=4.0)
    assert not verdict.passed


def test_network_is_unreachable():
    probe = _solution("""
import socket
try:
    socket.create_connection(('1.1.1.1', 53), timeout=2)
    return [1]
except OSError:
    return [0]
""")
    verdict = judge.judge_functional(probe, ENTRY, [judge.FunctionalTest(args=[[1], 1], expected=[0])], **_fast())
    assert verdict.passed, verdict


def test_host_files_are_not_readable():
    with tempfile.NamedTemporaryFile("w", dir=Path.home(), prefix="algsolve-secret-", delete=False) as fh:
        fh.write("host-secret")
        secret = fh.name
    try:
        probe = _solution(f"""
paths = [{secret!r}, '/etc/passwd', '/home', '/root']
seen = []
import os
for p in paths:
    seen.append(int(os.path.exists(p)))
return seen
""")
        verdict = judge.judge_functional(probe, ENTRY, [judge.FunctionalTest(args=[[1], 1], expected=[0, 0, 0, 0])], **_fast())
        assert verdict.passed, verdict
    finally:
        os.unlink(secret)


def test_task_directory_is_read_only():
    probe = _solution("""
try:
    open('/task/candidate.py', 'w').write('x')
    return [1]
except OSError:
    return [0]
""")
    verdict = judge.judge_functional(probe, ENTRY, [judge.FunctionalTest(args=[[1], 1], expected=[0])], **_fast())
    assert verdict.passed, verdict


def test_linked_list_and_tree_round_trip():
    source = """
class Solution:
    def reverse(self, head):
        prev = None
        while head:
            head.next, prev, head = prev, head, head.next
        return prev
"""
    tests = [judge.FunctionalTest(args=[{"__list_node__": [1, 2, 3]}], expected={"__list_node__": [3, 2, 1]})]
    verdict = judge.judge_functional(source, {"class": "Solution", "method": "reverse"}, tests, **_fast())
    assert verdict.passed, verdict
    invert = """
class Solution:
    def invert(self, root):
        if root:
            root.left, root.right = self.invert(root.right), self.invert(root.left)
        return root
"""
    tests = [judge.FunctionalTest(args=[{"__tree_node__": [4, 2, 7, 1, 3]}], expected={"__tree_node__": [4, 7, 2, None, None, 3, 1]})]
    verdict = judge.judge_functional(invert, {"class": "Solution", "method": "invert"}, tests, **_fast())
    assert verdict.passed, verdict


def test_in_place_argument_comparison():
    source = """
class Solution:
    def rotate(self, nums, k):
        k %= len(nums)
        nums[:] = nums[-k:] + nums[:-k]
"""
    tests = [judge.FunctionalTest(args=[[1, 2, 3, 4, 5], 2], expected=[4, 5, 1, 2, 3], compare="arg:0")]
    verdict = judge.judge_functional(source, {"class": "Solution", "method": "rotate"}, tests, **_fast())
    assert verdict.passed, verdict


def test_stdin_judge_passes_and_fails():
    tests = [judge.StdinTest("1 2\n", "3\n"), judge.StdinTest("5 7\n", "12")]
    good = "a, b = map(int, input().split())\nprint(a + b)\n"
    assert judge.judge_stdin(good, tests, **_fast()).passed
    bad = "a, b = map(int, input().split())\nprint(a * b)\n"
    verdict = judge.judge_stdin(bad, tests, **_fast())
    assert not verdict.passed and verdict.reason == judge.WRONG_ANSWER
    hang = "while True:\n    pass\n"
    verdict = judge.judge_stdin(hang, tests, **_fast())
    assert not verdict.passed and verdict.reason == judge.TIMEOUT
    crash = "raise SystemExit(3)\n"
    verdict = judge.judge_stdin(crash, tests, **_fast())
    assert not verdict.passed and verdict.reason == judge.RUNTIME_ERROR


def test_stdin_integer_tokens_must_match_exactly():
    assert not judge.tokens_equal("3", "3.0000001")
    assert judge.tokens_equal("0.333333", "0.3333331")
    assert not judge.tokens_equal("1 2", "1 2 3")


def test_checker_must_give_a_recognized_verdict():
    tests = [judge.StdinTest("4\n", "2 2\n")]
    candidate = "n = int(input())\nprint(1, n - 1)\n"
    accepting = (
        "import sys\n"
        "a, b = map(int, open(sys.argv[3]).read().split())\n"
        "n = int(open(sys.argv[1]).read())\n"
        "print(1 if a + b == n else 0)\n"
    )
    assert judge.judge_stdin(candidate, tests, checker_source=accepting, **_fast()).passed
    silent = "pass\n"
    verdict = judge.judge_stdin(candidate, tests, checker_source=silent, **_fast())
    assert not verdict.passed and verdict.reason == judge.CHECKER_ERROR
    partial_score = "print(100)\n"
    verdict = judge.judge_stdin(candidate, tests, checker_source=partial_score, **_fast())
    assert not verdict.passed and verdict.reason == judge.CHECKER_ERROR
    # A candidate that prints the checker's success token is still judged on content.
    forging = "print(1)\n"
    verdict = judge.judge_stdin(forging, tests, checker_source=accepting, **_fast())
    assert not verdict.passed
