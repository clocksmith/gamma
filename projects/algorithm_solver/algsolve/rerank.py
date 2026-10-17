"""Optional, local-only Doppler reranker. Scores require separate calibration."""
from __future__ import annotations
import hashlib
import copy
import json
import math
from pathlib import Path
import subprocess
import tempfile

from .records import LANE_ROOT


def scores_from_output(stdout: str, query: str, documents: list[str]) -> list[float]:
    # Doppler prints progress before its final JSON envelope. Accept only a
    # complete successful envelope with input-bound, finite, unique score rows.
    decoder = json.JSONDecoder()
    envelope = None
    offset = 0
    for line in stdout.splitlines(keepends=True):
        if line.startswith('{'):
            try:
                item, _ = decoder.raw_decode(stdout[offset:])
            except ValueError:
                item = None
            if isinstance(item, dict) and 'ok' in item and 'result' in item:
                envelope = item
        offset += len(line)
    if not envelope or envelope.get('ok') is not True:
        raise ValueError('Doppler did not return a successful result')
    result = envelope['result']
    output = result.get('output') or {}
    ranking = output.get('ranking') or []
    if output.get('query') != query or len(ranking) != len(documents):
        raise ValueError('Reranker result is not bound to the request')
    scores = [None] * len(documents)
    for row in ranking:
        index = row.get('index')
        score = row.get('score')
        if (type(index) is not int or not 0 <= index < len(documents) or scores[index] is not None
                or row.get('document') != documents[index] or type(score) not in (int, float)
                or not math.isfinite(score)):
            raise ValueError('Invalid, duplicated or mismatched reranker score')
        scores[index] = float(score)
    return scores


class DopplerReranker:
    def __init__(self, cli: Path, model_dir: Path, *, timeout: float = 90,
                 runtime_config: dict | None = None):
        self.cli = cli.resolve(strict=True)
        self.model_dir = model_dir.resolve(strict=True)
        manifest = self.model_dir / 'manifest.json'
        self.manifest_sha256 = hashlib.sha256(manifest.read_bytes()).hexdigest()
        self.model_id = json.loads(manifest.read_text())['modelId']
        self.timeout = timeout
        self.runtime_config = copy.deepcopy(runtime_config or {})
        inference = self.runtime_config.get('inference', {})
        if not isinstance(inference, dict) or 'rerank' in inference:
            raise ValueError('Runtime config cannot replace the rerank request')
        self.runtime_config_sha256 = hashlib.sha256(json.dumps(
            self.runtime_config, sort_keys=True, allow_nan=False).encode()).hexdigest()

    def __call__(self, query: str, documents: list[str]) -> list[float]:
        # Doppler's public rerank interface trims outer whitespace. Canonicalize
        # before dispatch so exact response binding checks the actual request.
        # Internal whitespace, statement content and candidate order stay intact.
        query, documents = query.strip(), [d.strip() for d in documents]
        if not query.strip() or not documents or any(not d.strip() for d in documents):
            raise ValueError('Reranker needs a query and nonempty documents')
        runtime = copy.deepcopy(self.runtime_config)
        runtime.setdefault('inference', {})['rerank'] = {'query': query, 'documents': documents}
        root = LANE_ROOT / 'runs' / 'reranker-calls'
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temp:
            path = Path(temp) / 'request.json'
            path.write_text(json.dumps({'request': {
                'workload': 'rerank', 'modelId': self.model_id, 'modelUrl': self.model_dir.as_uri(),
                'runtimeConfig': runtime}}))
            completed = subprocess.run(['node', str(self.cli), 'verify', '--config', str(path), '--surface', 'node'],
                                       cwd=temp, text=True, capture_output=True, timeout=self.timeout, check=True)
            return scores_from_output(completed.stdout, query, documents)
