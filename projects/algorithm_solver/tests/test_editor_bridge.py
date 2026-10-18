import hashlib
import json
from pathlib import Path
import sys
import time
import secrets
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
from algsolve.editor_bridge import Handler, Jobs


class BridgeContracts(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
        self.server.token = secrets.token_urlsafe(32)
        self.server.jobs = Jobs()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        for job in self.server.jobs.items.values():
            self.server.jobs.cancel(job)
        self.server.server_close()

    def request(self, path, body=None, method=None, origin='http://127.0.0.1:8874', token=True):
        headers = {'Origin':origin}
        if token: headers['Authorization'] = 'Bearer ' + self.server.token
        if body is not None: headers['Content-Type'] = 'application/json'
        request = Request(self.url + path, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        return response.status, response.read()

    def test_auth_origin_and_request_boundaries(self):
        self.assertEqual(self.request('/jobs', {}, token=False)[0],403)
        self.assertEqual(self.request('/jobs', {}, origin='https://unapproved.invalid')[0],403)
        self.assertEqual(self.request('/jobs', {'operation':'shell'})[0],400)
        self.assertEqual(self.request('/jobs', {'operation':'run','source':'a'*131072})[0],400)
        self.assertEqual(self.request('/pair?origin=https://unapproved.invalid', token=False)[0],403)

    def test_cancellation_releases_capacity_and_late_results_stay_cancelled(self):
        code, body = self.request('/jobs', {'operation':'run','language':'python','source':'while True: pass'})
        self.assertEqual(code,202)
        job_id=json.loads(body)['id']
        self.assertEqual(self.request('/jobs', {'operation':'run','language':'python','source':'print(1)'})[0],409)
        code,body=self.request('/jobs/'+job_id,method='DELETE')
        self.assertEqual(json.loads(body)['state'],'cancelled')
        self.assertFalse(self.server.jobs.items[job_id]['process'].is_alive())
        self.assertEqual(json.loads(self.request('/jobs/'+job_id)[1])['state'],'cancelled')
        self.assertEqual(self.request('/jobs', {'operation':'run','language':'python','source':'print(1)'})[0],202)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Requires real sandbox child processes')
    def test_cancel_running_sandbox_removes_children_and_task_files(self):
        code, body = self.request('/jobs', {'operation':'run','language':'python','source':'import time; time.sleep(60)'})
        job_id=json.loads(body)['id']
        worker=self.server.jobs.items[job_id]['process'].pid
        task=None
        deadline=time.monotonic()+2
        while time.monotonic()<deadline and task is None:
            for status in Path('/proc').glob('[0-9]*/status'):
                try:
                    if f'PPid:\t{worker}\n' not in status.read_text(): continue
                    args=(status.parent/'cmdline').read_bytes().split(b'\0')
                    task=next((Path(arg.decode()) for arg in args if arg.startswith(b'/tmp/algsolve-task-')),None)
                    if task: break
                except (FileNotFoundError, ProcessLookupError): pass
            if task is None: time.sleep(.02)
        self.assertIsNotNone(task, 'Must cancel an executing sandbox, not merely an unstarted worker')
        self.assertTrue(task.exists())
        self.assertEqual(json.loads(self.request('/jobs/'+job_id,method='DELETE')[1])['state'],'cancelled')
        self.assertFalse(task.exists(), 'Cancellation must remove submitted source files')
        self.assertFalse(self.server.jobs.items[job_id]['process'].is_alive())
        payload={'operation':'run','language':'javascript','source':'console.log(7)'}
        code,body=self.request('/jobs',payload)
        next_id=json.loads(body)['id']
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            result=json.loads(self.request('/jobs/'+next_id)[1])
            if result['state']!='running': break
            time.sleep(.02)
        self.assertEqual(result['state'],'complete')
        self.assertEqual(result['result']['stdout'],'7\n')
        self.assertEqual(result['result']['request_binding']['request_sha256'],hashlib.sha256(json.dumps(payload).encode()).hexdigest())
