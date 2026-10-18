"""Loopback-only, explicitly paired editor bridge to bounded research jobs."""
import argparse
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import multiprocessing
from pathlib import Path
import secrets
import signal
import threading
import time
from urllib.parse import urlparse, parse_qs
from .editor_task import run_job

ORIGINS = {'https://256.one', 'https://one256.web.app', 'http://127.0.0.1:8874', 'http://localhost:8874'}
MAX_BODY = 131072


class Jobs:
    def __init__(self, approved_library=None):
        self.items = {}
        self.lock = threading.Lock()
        self.context = multiprocessing.get_context('spawn')
        self.approved_library = str(Path(approved_library).resolve()) if approved_library else None
        if self.approved_library:
            from .approved_library import ApprovedLibrary
            ApprovedLibrary.load(self.approved_library)

    def poll(self, job):
        if job.get('result'):
            return job['result']
        if job['pipe'].poll():
            try:
                job['result'] = job['pipe'].recv()
            except EOFError:
                job['result'] = {'state': 'failed', 'error': 'Worker exited without a result'}
            job['pipe'].close()
            job['process'].join(timeout=1)
            if job['process'].is_alive():
                job['process'].terminate()
                job['process'].join(timeout=2)
        elif not job['process'].is_alive():
            job['pipe'].close()
            job['process'].join()
            job['result'] = {'state': 'failed', 'error': 'Worker exited without a result'}
        elif time.monotonic() - job['started'] > 90:
            self.cancel(job, 'timeout')
        return job.get('result', {'state': 'running'})

    def cancel(self, job, state='cancelled'):
        if job.get('result'):
            return job['result']
        process = job['process']
        process.terminate()
        process.join(timeout=2)
        if process.is_alive():
            process.kill()
            process.join(timeout=2)
        job['pipe'].close()
        job['result'] = {'state': state}
        return job['result']

    def start(self, payload, request_digest):
        with self.lock:
            for job in self.items.values():
                if self.poll(job)['state'] == 'running':
                    raise RuntimeError('Bridge busy; wait or cancel the current job')
            self.items = {key: job for key, job in self.items.items() if time.monotonic() - job['started'] < 120}
            if len(self.items) >= 16:
                raise RuntimeError('Recent job limit reached')
            parent, child = self.context.Pipe(duplex=False)
            process = self.context.Process(target=run_job, args=(payload, child, request_digest, self.approved_library), daemon=True)
            process.start()
            child.close()
            job_id = secrets.token_hex(16)
            self.items[job_id] = {'process': process, 'pipe': parent, 'started': time.monotonic()}
            return job_id

    def reap(self):
        while True:
            time.sleep(1)
            with self.lock:
                for job in self.items.values():
                    self.poll(job)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Never put tokens or source text in access logs.

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def send(self, status, value, content_type='application/json'):
        data = value.encode() if isinstance(value, str) else json.dumps(value).encode()
        self.send_response(status)
        origin = self.headers.get('Origin')
        if origin in ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def valid_host(self):
        return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

    def authorized(self):
        return (self.valid_host() and self.headers.get('Origin') in ORIGINS and
                hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + self.server.token))

    def do_OPTIONS(self):
        self.send(204 if self.valid_host() and self.headers.get('Origin') in ORIGINS else 403, '')

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/pair' and self.valid_host():
            origin = parse_qs(parsed.query).get('origin', [''])[0]
            if origin not in ORIGINS:
                self.send(403, {'error': 'Unknown editor origin'})
                return
            # Explicit local click grants only this fixed origin; no token in URL/storage.
            page = ('<!doctype html><meta name="viewport" content="width=device-width"><title>Connect Gamma</title>'
                    '<h1>Connect the editor to Gamma</h1><p>This allows the editor to run bounded code and retrieve stored solutions on your machine.</p>'
                    '<button id="connect">Connect</button><script>document.getElementById("connect").onclick=()=>{'
                    f'window.opener?.postMessage({{type:"gamma-paired",token:{json.dumps(self.server.token)}}},{json.dumps(origin)});'
                    'window.close();};</script>')
            self.send(200, page, 'text/html; charset=utf-8')
            return
        if not self.authorized():
            self.send(403, {'error': 'Pair this editor first'})
            return
        job_id = parsed.path.removeprefix('/jobs/')
        with self.server.jobs.lock:
            job = self.server.jobs.items.get(job_id)
            result = self.server.jobs.poll(job) if job else {'error': 'Unknown job'}
        self.send(200 if job else 404, result)

    def do_POST(self):
        if not self.authorized():
            self.send(403, {'error': 'Pair this editor first'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if self.path != '/jobs' or not 0 < length <= MAX_BODY or self.headers.get('Content-Type') != 'application/json':
                raise ValueError('Invalid request size, path or content type')
            body = self.rfile.read(length)
            payload = json.loads(body)
            if not isinstance(payload, dict) or payload.get('operation') not in {'run', 'retrieve', 'challenge'}:
                raise ValueError('Unknown operation')
            job_id = self.server.jobs.start(payload, hashlib.sha256(body).hexdigest())
            self.send(202, {'id': job_id})
        except RuntimeError as error:
            self.send(409, {'error': str(error)})
        except (ValueError, TypeError) as error:
            self.send(400, {'error': str(error)})

    def do_DELETE(self):
        if not self.authorized():
            self.send(403, {'error': 'Pair this editor first'})
            return
        with self.server.jobs.lock:
            job = self.server.jobs.items.get(self.path.removeprefix('/jobs/'))
            result = self.server.jobs.cancel(job) if job else {'error': 'Unknown job'}
        self.send(200 if job else 404, result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8875)
    parser.add_argument('--approved-library', type=Path,
                        help='Only return independently qualified, source-bound stored answers')
    args = parser.parse_args()
    def stop(*_):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.token = secrets.token_urlsafe(32)
    server.jobs = Jobs(approved_library=args.approved_library)
    threading.Thread(target=server.jobs.reap, daemon=True).start()
    print('[run-contract] run_name=editor-bridge pairs_input_spec=explicit-editor-requests resume_from=none '
          'resume_stage=none decode=none eval_dataset_paths=public-examples device=cpu schedule=single-job '
          'runtime_mode=cpu sweep_mode=after_train', flush=True)
    print(f'Gamma bridge listening on loopback port {args.port}; pair from the editor.', flush=True)
    try:
        server.serve_forever()
    finally:
        with server.jobs.lock:
            for job in server.jobs.items.values():
                server.jobs.cancel(job)
        server.server_close()


if __name__ == '__main__':
    main()
