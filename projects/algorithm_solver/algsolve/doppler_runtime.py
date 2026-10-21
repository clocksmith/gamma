"""Retained local Doppler embeddings/reranking. No downloads or CPU fallback."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import tempfile
import threading
import time

import numpy as np

from .embed import MAX_TOKENS, QUERY_INSTRUCTION
from .records import LANE_ROOT
from .rerank import scores_from_output

WORKER = Path(__file__).with_name('doppler_worker.mjs')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class DopplerRuntime:
    """Own one subprocess and both model handles; close on errors or cancellation."""
    def __init__(self, root, embedding_model, reranker_model=None, *, timeout=90,
                 embedding_config=None, reranker_config=None, log_dir=None):
        if not 0 < timeout <= 600:
            raise ValueError('Doppler timeout must be in (0, 600]')
        root = Path(root).resolve(strict=True)
        (root / 'src/client/doppler-api.js').resolve(strict=True)
        self.config = {'root': str(root), 'max_tokens': MAX_TOKENS}
        for role, path, runtime_config in (
                ('embedding', embedding_model, embedding_config),
                ('rerank', reranker_model, reranker_config)):
            if path is None:
                continue
            path = Path(path).resolve(strict=True)
            self.config[role] = {'path': str(path), 'manifest_sha256': sha(path/'manifest.json'),
                                 'runtime_config': json.loads(json.dumps(runtime_config or {}, allow_nan=False))}
        revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
        diff = subprocess.check_output(['git', '-C', str(root), 'diff', 'HEAD', '--', 'src'])
        self.identity = {
            'runtime': 'doppler', 'revision': revision,
            'source_diff_sha256': hashlib.sha256(diff).hexdigest(),
            'worker_sha256': sha(WORKER), 'max_tokens': MAX_TOKENS,
            'query_instruction': QUERY_INSTRUCTION,
            'models': {role: {k: v for k, v in self.config[role].items() if k != 'path'}
                       for role in ('embedding', 'rerank') if role in self.config},
        }
        self.timeout = timeout
        self.log_dir = Path(log_dir or LANE_ROOT/'runs/doppler-runtime')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.process = None
        self.last_receipt = None
        self._sequence = 0
        self._lock = threading.Lock()
        self._closed = False
        self._buffer = b''

    def _start(self):
        self._directory = Path(tempfile.mkdtemp(prefix='session-', dir=self.log_dir))
        config_path = self._directory/'config.json'
        config_path.write_text(json.dumps(self.config, allow_nan=False))
        self._log = (self._directory/'stderr.log').open('wb')
        self.process = subprocess.Popen(
            ['node', str(WORKER), str(config_path)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=self._log, start_new_session=True, bufsize=0)

    def _request(self, operation, **payload):
        with self._lock:
            if self._closed:
                raise RuntimeError('Doppler session is closed')
            if self.process is None:
                self._start()
            self._sequence += 1
            request = dict(id=self._sequence, operation=operation, **payload)
            raw = json.dumps(request, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            expected_hash = hashlib.sha256(raw.encode()).hexdigest()
            started = time.monotonic()
            try:
                if len(raw.encode()) > 1_000_000:
                    raise ValueError('Doppler request exceeds one MB')
                # Pipes are unbuffered: write() may be partial for large batches.
                data = (raw + '\n').encode()
                os.set_blocking(self.process.stdin.fileno(), False)
                with selectors.DefaultSelector() as writer:
                    writer.register(self.process.stdin, selectors.EVENT_WRITE)
                    while data:
                        remaining = self.timeout - (time.monotonic() - started)
                        if remaining <= 0 or not writer.select(remaining):
                            raise TimeoutError('Doppler input timed out')
                        try:
                            written = os.write(self.process.stdin.fileno(), data)
                        except BlockingIOError:
                            continue
                        data = data[written:]
                with selectors.DefaultSelector() as selector:
                    selector.register(self.process.stdout, selectors.EVENT_READ)
                    while b'\n' not in self._buffer:
                        remaining = self.timeout - (time.monotonic() - started)
                        if remaining <= 0 or not selector.select(remaining):
                            raise TimeoutError('Doppler request timed out')
                        chunk = os.read(self.process.stdout.fileno(), 65536)
                        if not chunk:
                            raise RuntimeError(f'Doppler exited; see {self._directory}/stderr.log')
                        self._buffer += chunk
                        if len(self._buffer) > 16_000_000:
                            raise ValueError('Doppler response exceeds limit')
                line, self._buffer = self._buffer.split(b'\n', 1)
                response = json.loads(line)
                if response.get('id') != request['id']:
                    raise ValueError('Stale or mismatched Doppler response')
                if response.get('ok') is not True:
                    raise RuntimeError(response.get('error', 'Doppler failed'))
                result = response['result']
                if result.get('input_sha256') != expected_hash:
                    raise ValueError('Doppler result input hash differs')
                self.last_receipt = {k: v for k, v in result.items() if k != 'output'}
                self.last_receipt['total_ms'] = (time.monotonic() - started) * 1000
                return result['output']
            except BaseException:
                self.close()
                raise

    def encode(self, texts, *, query=False, instruction=None, batch_size=16):
        if not 1 <= batch_size <= 32:
            raise ValueError('Doppler batch size must be 1–32')
        if not texts:
            return np.zeros((0, 1024), dtype=np.float32)
        if any(not isinstance(t, str) or not t.strip() for t in texts):
            raise ValueError('Embedding needs nonempty text')
        prefix = (instruction or QUERY_INSTRUCTION) if query else ''
        vectors = []
        for start in range(0, len(texts), batch_size):
            batch = [prefix + t for t in texts[start:start + batch_size]]
            output = self._request('embedding', texts=batch)
            if output.get('texts') != batch or len(output.get('rows', [])) != len(batch):
                self.close()
                raise ValueError('Doppler embedding rows do not match input')
            try:
                matrix = np.asarray([r['embedding'] for r in output['rows']], dtype=np.float32)
                if matrix.shape != (len(batch), 1024) or not np.isfinite(matrix).all():
                    raise ValueError('Invalid vector dimensions or values')
                norms = np.linalg.norm(matrix, axis=1)
                if not np.isfinite(norms).all() or np.any(norms <= 0):
                    raise ValueError('Invalid vector norms')
            except (ValueError, KeyError, TypeError):
                self.close()
                raise ValueError('Doppler returned invalid Qwen embedding vectors')
            self.last_receipt['embedding_rows'] = [
                {k: row.get(k) for k in ('tokens', 'truncated', 'backend')}
                for row in output['rows']]
            vectors.append(matrix / norms[:, None])
        return np.concatenate(vectors)

    def rerank(self, query, documents):
        query, documents = query.strip(), [d.strip() for d in documents]
        output = self._request('rerank', query=query, documents=documents)
        try:
            scores = scores_from_output(json.dumps({'ok': True, 'result': {'output': output}}),
                                        query, documents)
            self.last_receipt['backend'] = output.get('backend')
            return scores
        except BaseException:
            self.close()
            raise

    def close(self):
        if self._closed:
            return
        self._closed = True
        if self.process is None:
            return
        self.process.stdin.close()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait()
        self.process.stdout.close()
        self._log.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
