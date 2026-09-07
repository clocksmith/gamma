"""Retain one bounded synthetic runner-test attempt, including failed attempts."""
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path.cwd()
OWN = Path(__file__).resolve().parent
attempt = OWN / sys.argv[1]
attempt.mkdir()
temporary = attempt / "tmp"
temporary.mkdir()
names = [
    "tools/fx2_causal_field_preceding_gate_v2.py",
    "tests/test_fx2_causal_field_preceding_gate_v2.py",
    "tools/fx2_causal_field_preceding_replay_v1.py",
    "tools/causal_field_preceding_adapter250k_v1.py",
    "tools/causal_field_preceding_selector_v1.py",
    "tools/causal_field_wrt_adapter_v1.py",
    "tools/causal_field_dependency_v1.py",
    "tools/causal_field_parent_coder_v1.py",
    "tools/wrt_exact.py",
    "tools/fx2_causal_field_replay_v1.py",
    "lib/driver.py", "lib/artifacts.py",
]
def ref(path):
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}
sources = []
for name in names:
    source = ROOT / name
    target = attempt / "source" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    sources.append(ref(source))
(attempt / "sources.json").write_text(json.dumps(sources, indent=2) + "\n")
def limits():
    os.sched_setaffinity(0, {5})
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (60,) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2,) * 2)
env = {**os.environ, "TMPDIR": str(temporary), "PYTHONDONTWRITEBYTECODE": "1",
       "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
       "PYTHONHASHSEED": "0",
       "GAMMA_PRECEDING_GATE_SYNTHETIC_RETAIN": str(attempt / "retained")}
command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
           "-p", "test_fx2_causal_field_preceding_gate_v2.py", "-v"]
started = time.time()
clock = time.monotonic()
peak_scratch = 0
failure = None
with (attempt / "stdout").open("xb") as stdout, (attempt / "stderr").open("xb") as stderr:
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                               preexec_fn=limits, start_new_session=True)
    while process.poll() is None:
        scratch = sum(p.stat().st_size for p in OWN.rglob("*") if p.is_file())
        peak_scratch = max(peak_scratch, scratch)
        if time.monotonic() - clock > 120 or scratch > 32 * 1024**2:
            failure = "wall_budget" if time.monotonic() - clock > 120 else "scratch_budget"
            os.killpg(process.pid, signal.SIGKILL)
            break
        time.sleep(0.1)
    returncode = process.wait()
usage = resource.getrusage(resource.RUSAGE_CHILDREN)
record = {"command": command, "started_epoch": started, "wall_seconds": time.monotonic() - clock,
          "returncode": returncode, "budget_failure": failure, "cpu_set": [5],
          "aggregate_child_cpu_seconds": usage.ru_utime + usage.ru_stime,
          "child_peak_rss_kib": usage.ru_maxrss, "peak_sampled_scratch_bytes": peak_scratch,
          "timing_authority": "shared-host synthetic tests",
          "sources_unchanged": all(ref(ROOT / r["path"]) == r for r in sources),
          "corpus_bytes_read": 0, "complete_package_bytes": None, "objective_credit_bytes": 0}
(attempt / "execution.json").write_text(json.dumps(record, indent=2) + "\n")
files = [ref(p) for p in sorted(attempt.rglob("*")) if p.is_file()]
(attempt / "inventory.json").write_text(json.dumps(files, indent=2) + "\n")
print(json.dumps(record))
sys.exit(returncode or bool(failure) or not record["sources_unchanged"])
