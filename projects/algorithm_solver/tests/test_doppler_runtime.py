from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from algsolve.doppler_runtime import DopplerRuntime
from algsolve.embed import QUERY_INSTRUCTION


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'src/client').mkdir(parents=True)
        (self.root/'src/client/doppler-api.js').touch()
        (self.root/'manifest.json').write_text('{"modelId":"fixture"}')
        with patch('algsolve.doppler_runtime.subprocess.check_output', return_value=b''):
            self.runtime = DopplerRuntime(self.root, self.root, self.root,
                                          timeout=.2, log_dir=self.root/'logs')
        self.runtime.last_receipt = {}
        self.addCleanup(self.runtime.close)

    def test_query_instruction_normalization_and_empty_batch(self):
        def request(operation, **payload):
            self.assertEqual(operation, 'embedding')
            self.assertEqual(payload['texts'], [QUERY_INSTRUCTION+'request'])
            return {'texts': payload['texts'], 'rows': [{'embedding': [2.] + [0.]*1023}]}
        with patch.object(self.runtime, '_request', side_effect=request) as invoke:
            actual = self.runtime.encode(['request'], query=True)
            self.assertEqual(actual.shape, (1, 1024))
            self.assertEqual(actual[0, 0], 1.)
            self.assertEqual(self.runtime.encode([]).shape, (0, 1024))
            self.assertEqual(invoke.call_count, 1)

    def test_bad_vectors_and_wrong_text_never_escape(self):
        for output in [
            {'texts': ['wrong'], 'rows': []},
            {'texts': ['q'], 'rows': [{'embedding': [0.]*1024}]},
            {'texts': ['q'], 'rows': [{'embedding': [float('nan')]*1024}]},
            {'texts': ['q'], 'rows': [{'embedding': [1., 2.]}]},
        ]:
            with self.subTest(output=str(output)[:80]), patch.object(self.runtime, '_request', return_value=output):
                with self.assertRaises(ValueError):
                    self.runtime.encode(['q'])

    def test_surface_and_shared_code_are_bound_to_runtime_identity(self):
        with patch('algsolve.doppler_runtime.subprocess.check_output', return_value=b''):
            browser = DopplerRuntime(self.root, self.root, surface='browser', log_dir=self.root/'logs')
        self.addCleanup(browser.close)
        self.assertEqual(browser.identity['surface'], 'browser')
        self.assertEqual(self.runtime.identity['surface'], 'node')
        self.assertEqual(browser.identity['session_sha256'], self.runtime.identity['session_sha256'])
        self.assertNotEqual(browser.identity['worker_sha256'], self.runtime.identity['worker_sha256'])
        with self.assertRaisesRegex(ValueError, 'surface'):
            DopplerRuntime(self.root, self.root, surface='unknown')

    def test_rerank_returns_original_order_and_rejects_wrong_documents(self):
        rows = [{'index': 1, 'document': 'b', 'score': 2.},
                {'index': 0, 'document': 'a', 'score': 1.}]
        with patch.object(self.runtime, '_request', return_value={'query': 'q', 'ranking': rows}) as invoke:
            self.assertEqual(self.runtime.rerank(' q ', [' a ', 'b']), [1., 2.])
            invoke.assert_called_once_with('rerank', query='q', documents=['a', 'b'])
            rows[0]['document'] = 'different'
            with self.assertRaises(ValueError):
                self.runtime.rerank('q', ['a', 'b'])

    def start_fake(self, body):
        script = self.root/'worker.py'
        script.write_text('import sys,json,hashlib,time\n'+body)
        self.runtime._directory = self.root
        self.runtime._log = (self.root/'stderr.log').open('wb')
        self.runtime.process = subprocess.Popen(
            [sys.executable, str(script)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.runtime._log, bufsize=0, start_new_session=True)

    def test_process_is_reused_and_request_hash_is_checked(self):
        self.start_fake(
            'for line in sys.stdin:\n'
            ' r=json.loads(line)\n'
            ' h=hashlib.sha256(line.strip().encode()).hexdigest()\n'
            ' print(json.dumps({"id":r["id"],"ok":True,"result":{"input_sha256":h,"output":{"pid":1}}}),flush=True)\n')
        pid = self.runtime.process.pid
        self.assertEqual(self.runtime._request('embedding', texts=['q']), {'pid': 1})
        self.assertEqual(self.runtime._request('embedding', texts=['r']), {'pid': 1})
        self.assertEqual(self.runtime.process.pid, pid)
        self.runtime.close()
        self.assertIsNotNone(self.runtime.process.poll())
        with self.assertRaises(RuntimeError):
            self.runtime._request('embedding', texts=['q'])

    def test_stale_result_terminates_worker(self):
        self.start_fake(
            'for line in sys.stdin:\n'
            ' print(json.dumps({"id":999,"ok":True,"result":{}}),flush=True)\n')
        with self.assertRaisesRegex(ValueError, 'Stale'):
            self.runtime._request('embedding', texts=['q'])
        self.assertIsNotNone(self.runtime.process.poll())

    def test_timeout_terminates_worker_without_fallback(self):
        self.start_fake('sys.stdin.readline()\ntime.sleep(10)\n')
        with self.assertRaises(TimeoutError):
            self.runtime._request('embedding', texts=['q'])
        self.assertIsNotNone(self.runtime.process.poll())

    @unittest.skipUnless(shutil.which('node'), 'Node is required for the stdio adapter')
    def test_worker_passes_text_and_explicit_input_ids_to_doppler(self):
        self.runtime.timeout = 5
        (self.root/'package.json').write_text('{"type":"module"}')
        (self.root/'src/tooling').mkdir()
        (self.root/'src/tooling/node-file-fetch.js').write_text(
            'export function installNodeFileFetchShim() {}')
        (self.root/'src/client/doppler-api.js').write_text("""
export async function load() {
  return {
    advanced: { tokenizeText: () => [17, 23] },
    async embedWithEvidence(text, options) {
      if (typeof text !== 'string' || options?.inputIds?.join() !== '17,23')
        throw new Error('Wrong Doppler embedding input contract');
      return { embedding: [1, ...Array(1023).fill(0)], tokens: [17,23],
               backendIdentity: { backend: 'fixture' } };
    },
    async unload() {},
  };
}
""")
        self.assertEqual(self.runtime.encode(['actual text'])[0, 0], 1.)
        self.assertEqual(self.runtime.last_receipt['embedding_rows'][0]['tokens'], 2)


if __name__ == '__main__':
    unittest.main()
