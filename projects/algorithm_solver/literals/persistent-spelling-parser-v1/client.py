"""Supplied-input sequential client. No corpus loader or engine installation."""
import json
import math
import os
from pathlib import Path
import selectors
import subprocess
import threading
import time

HERE = Path(__file__).resolve().parent
REQUEST_LIMIT = 4 * 1024 * 1024
RESPONSE_LIMIT = 16 * 1024 * 1024
ERRORS = {'ASCII_CONTRACT', 'LEXICAL_PARSE', 'LEXICAL_STDOUT_LIMIT',
          'STRUCTURAL_PARSE', 'UNSUPPORTED_SOLVE_BODY', 'REQUEST_LIMIT',
          'REQUEST_SCHEMA', 'RESPONSE_LIMIT', 'INTERNAL_ERROR'}


class Client:
    def __init__(self, timeout=10.0):
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('Finite positive request timeout required')
        self.timeout = timeout
        self._request_lock = threading.Lock()
        self.command = ['/usr/bin/node', '--max-old-space-size=256', str(HERE/'service.cjs')]
        self.process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, start_new_session=False)
        self.closed = False; self.ident = 0
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)

    def close(self):
        if self.closed: return
        self.closed = True
        try:
            if self.process.poll() is None: self.process.kill()
            self.process.wait(timeout=1.0)
        finally:
            for stream in (self.process.stdin, self.process.stdout): stream.close()

    def __enter__(self): return self
    def __exit__(self, exc_type, error, traceback):
        try: self.close()
        except BaseException:
            if error is None: raise
            error.add_note('Parser cleanup failed; original failure retained')

    def _failure(self, reason):
        return subprocess.CalledProcessError(1, self.command, stderr=reason)

    def request(self, texts):
        if not self._request_lock.acquire(blocking=False):
            self.close()
            raise self._failure('CONCURRENT_REQUEST')
        try: return self._request(texts)
        finally: self._request_lock.release()

    def _request(self, texts):
        if self.closed: raise RuntimeError('Parser client is closed; no retry')
        try:
            if not isinstance(texts, dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in texts.items()):
                raise self._failure('REQUEST_SCHEMA')
            self.ident += 1
            payload = json.dumps({'id':self.ident, 'texts':texts}, separators=(',',':'), ensure_ascii=True).encode()
            if len(payload) > REQUEST_LIMIT: raise self._failure('REQUEST_LIMIT')
            payload += b'\n'; sent = 0; response = bytearray(); deadline = time.monotonic()+self.timeout
            with selectors.DefaultSelector() as events:
                events.register(self.process.stdin, selectors.EVENT_WRITE)
                events.register(self.process.stdout, selectors.EVENT_READ)
                while True:
                    remaining = deadline-time.monotonic()
                    if remaining <= 0: raise subprocess.TimeoutExpired(self.command, self.timeout)
                    ready = events.select(remaining)
                    if not ready: raise subprocess.TimeoutExpired(self.command, self.timeout)
                    for key, _ in ready:
                        if key.fileobj is self.process.stdin:
                            try: count = os.write(key.fd, payload[sent:sent+65536])
                            except BrokenPipeError: raise self._failure('SERVICE_EXIT') from None
                            sent += count
                            if sent == len(payload): events.unregister(self.process.stdin)
                        else:
                            block = os.read(key.fd, 65536)
                            if not block: raise self._failure('SERVICE_EXIT')
                            response.extend(block)
                            if len(response) > RESPONSE_LIMIT: raise self._failure('RESPONSE_LIMIT')
                            if b'\n' not in response: continue
                            if response.count(b'\n') != 1 or not response.endswith(b'\n'):
                                raise self._failure('RESPONSE_SCHEMA')
                            try: value = json.loads(response)
                            except (ValueError, UnicodeError): raise self._failure('RESPONSE_SCHEMA') from None
                            if not isinstance(value,dict) or type(value.get('id')) is not int or value['id'] != self.ident:
                                raise self._failure('RESPONSE_SCHEMA')
                            if value.get('ok') is False:
                                if set(value) != {'id','ok','error'} or value['error'] not in ERRORS:
                                    raise self._failure('RESPONSE_SCHEMA')
                                raise self._failure(value['error'])
                            if value.get('ok') is not True or set(value) != {'id','ok','bodies'}:
                                raise self._failure('RESPONSE_SCHEMA')
                            bodies = value['bodies']
                            # Preserve old JavaScript {} assignment semantics:
                            # '__proto__' is not emitted as an own output key.
                            if not isinstance(bodies,dict) or set(bodies) != set(texts)-{'__proto__'} or not all(
                                    isinstance(row,list) and row and all(isinstance(s,str) and s for s in row)
                                    for row in bodies.values()): raise self._failure('RESPONSE_SCHEMA')
                            return bodies
        except BaseException as error:
            try: self.close()
            except BaseException: error.add_note('Parser cleanup failed; original failure retained')
            raise

    def banned(self, texts):
        """Same one-call insertion order/512-item chunks and set union as41."""
        try:
            result = set(texts.values()); items = list(texts.items())
            for start in range(0, len(items), 512):
                for bodies in self.request(dict(items[start:start+512])).values(): result.update(bodies)
            return result
        except BaseException as error:
            try: self.close()
            except BaseException: error.add_note('Parser cleanup failed; original failure retained')
            raise
