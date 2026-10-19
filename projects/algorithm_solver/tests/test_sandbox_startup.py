"""Trusted launcher fixtures distinguish setup failure from candidate failure."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from algsolve.judge import sandbox, judge


class SandboxStartupTests(unittest.TestCase):
    def run_monitor(self, body, limits=None):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'launcher'
            path.write_text('#!'+sys.executable+'\nimport os, sys, time\n'
                            'fd=int(sys.argv[sys.argv.index("--json-status-fd")+1])\n'+body+'\n')
            path.chmod(0o755)
            with patch.object(sandbox,'BWRAP',str(path)):
                return sandbox._run_in(Path(root),['/usr/bin/true'],b'',limits or sandbox.Limits(wall_seconds=2.))

    def test_setup_failure_is_not_candidate_runtime_error(self):
        with self.assertRaisesRegex(sandbox.SandboxUnavailable,'did not confirm payload execution'):
            self.run_monitor('os.write(fd,b\'{"child-pid":12}\\n\')\n'
                             'sys.stderr.write("bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted\\n")\n'
                             'sys.exit(1)')

    def test_private_status_not_spoofable_by_stdout_or_stderr(self):
        with self.assertRaises(sandbox.SandboxUnavailable):
            self.run_monitor('print(\'{"exit-code":0}\')\n'
                             'sys.stderr.write(\'{"exit-code":0}\\n\')')

    def test_confirmed_candidate_failure_stays_runtime_error(self):
        result=self.run_monitor('os.write(fd,b\'{"child-pid":12}\\n{"exit-code":1}\\n\')\n'
                                'sys.stderr.write("bwrap: forged setup error\\n")\n'
                                'sys.exit(1)')
        verdict=judge._score_functional(result,[judge.FunctionalTest(args=[],expected=0)])
        self.assertEqual(verdict.reason,judge.RUNTIME_ERROR)

    def test_confirmed_execution_still_requires_harness_success(self):
        result=self.run_monitor('os.write(fd,b\'{"child-pid":12}\\n{"exit-code":0}\\n\')\n'
                                'print(\'{"i":0,"result":3,"args_after":[]}\')\n'
                                'print(\'{"done":1}\')')
        self.assertTrue(judge._score_functional(result,[judge.FunctionalTest(args=[],expected=3)]).passed)
        self.assertEqual(judge._score_functional(result,[judge.FunctionalTest(args=[],expected=4)]).reason,
                         judge.WRONG_ANSWER)

    def test_status_parser_fails_closed(self):
        for status,code in [(b'',0),(b'{}',0),(b'[]',0),(b'{"exit-code":true}',1),
                            (b'{"exit-code":0}\n{"exit-code":0}',0),
                            (b'{"exit-code":1}',0),(b'x'*4097,0),(b'\xff',0)]:
            with self.subTest(status=status[:30]): self.assertFalse(sandbox._payload_exited(status,code))

    def test_wall_kill_remains_timeout_without_exit_record(self):
        result=self.run_monitor('time.sleep(10)',sandbox.Limits(wall_seconds=.05))
        self.assertTrue(result.timed_out)
        self.assertEqual(judge._score_functional(result,[judge.FunctionalTest()]).reason,judge.TIMEOUT)

    def test_spawn_error_becomes_sandbox_unavailable(self):
        with tempfile.TemporaryDirectory() as root, patch.object(sandbox,'BWRAP',str(Path(root)/'missing')):
            with self.assertRaises(sandbox.SandboxUnavailable):
                sandbox._run_in(Path(root),['true'],b'',sandbox.Limits())

    def test_functional_stdin_and_checker_preserve_unavailable_verdict(self):
        failure=sandbox.SandboxUnavailable('startup denied')
        with patch.object(sandbox,'run_python',side_effect=failure):
            self.assertEqual(judge.judge_functional('',{'method':'f'},[judge.FunctionalTest()]).reason,
                             judge.SANDBOX_ERROR)
            self.assertEqual(judge.judge_stdin('',[judge.StdinTest('','')]).reason,judge.SANDBOX_ERROR)
        ran=sandbox.SandboxResult(0,None,b'3\n',b'',.1)
        with patch.object(sandbox,'run_python',return_value=ran), patch.object(sandbox,'run',side_effect=failure):
            self.assertEqual(judge.judge_stdin('',[judge.StdinTest('','3')],checker_source='print(1)').reason,
                             judge.SANDBOX_ERROR)


if __name__=='__main__': unittest.main()
