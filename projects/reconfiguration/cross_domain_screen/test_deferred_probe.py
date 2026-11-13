"""CPU-only admission tests; Linux additionally checks actual inherited flock."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("scheduler", HERE / "run_deferred_probe.py")
scheduler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scheduler)


class AdmissionTests(unittest.TestCase):
    def test_guard_requires_fresh_inactive_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guard.json"
            config = {"serviceGuardPath": str(path), "serviceGuardMaxAgeMs": 15000}
            body = dict(allowed=True, stageAdmitted=0, providerState="inactive", providerSubState="dead", providerMainPID=0, checkedAt=scheduler.utc())
            path.write_text(json.dumps(body))
            self.assertTrue(scheduler.guard_observation(config)["ready"])
            for patch in ({"providerMainPID": 12}, {"providerState": "active"}, {"stageAdmitted": False}, {"providerMainPID": False}, {"checkedAt": "2000-01-01T00:00:00Z"}):
                path.write_text(json.dumps({**body, **patch}))
                self.assertFalse(scheduler.guard_observation(config)["ready"])

    def test_exclusive_waits_for_shared_holder(self):
        with tempfile.NamedTemporaryFile() as handle:
            fcntl.flock(handle, fcntl.LOCK_SH)
            code = "import fcntl,sys; f=open(sys.argv[1],'a+b'); print('waiting',flush=True); fcntl.flock(f,fcntl.LOCK_EX); print('acquired',flush=True)"
            child = subprocess.Popen([sys.executable, "-c", code, handle.name], stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(), "waiting")
                with self.assertRaises(subprocess.TimeoutExpired):
                    child.wait(timeout=.1)
                fcntl.flock(handle, fcntl.LOCK_UN)
                stdout, _ = child.communicate(timeout=5)
                self.assertEqual(stdout.strip(), "acquired")
                self.assertEqual(child.returncode, 0)
            finally:
                if child.poll() is None:
                    child.terminate()
                    child.wait()
                child.stdout.close()

    @unittest.skipUnless(sys.platform == "linux", "Linux fdinfo admission boundary")
    def test_child_inherited_fd_requires_matching_exclusive_flock(self):
        code = "const m=await import(process.argv[1]); try {console.log(JSON.stringify(await m.checkInheritedExclusiveLock(Number(process.argv[2]),process.argv[3])));} catch(e){console.error(e.message);process.exitCode=2;}"
        with tempfile.NamedTemporaryFile() as handle, tempfile.NamedTemporaryFile() as other:
            def check(path):
                return subprocess.run(["node", "--input-type=module", "-e", code, (HERE / "probe_completion_gate.mjs").as_uri(), str(handle.fileno()), path], pass_fds=(handle.fileno(),), capture_output=True, text=True)
            self.assertEqual(check(handle.name).returncode, 2)
            fcntl.flock(handle, fcntl.LOCK_SH)
            self.assertEqual(check(handle.name).returncode, 2)
            fcntl.flock(handle, fcntl.LOCK_EX)
            admitted = check(handle.name)
            self.assertEqual(admitted.returncode, 0, admitted.stderr)
            self.assertFalse(json.loads(admitted.stdout)["globalIsolationQualified"])
            self.assertEqual(check(other.name).returncode, 2)


if __name__ == "__main__":
    unittest.main()
