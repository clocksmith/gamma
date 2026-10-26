"""Metadata-only BITS discovery over the existing known-corpus vector index.

Returns candidate identities for a person to select, never source code, tests,
an automatic accepted answer, or a recognition-qualification claim.
"""
import hashlib
import json
from pathlib import Path
import re
import threading

import numpy as np

from .doppler_runtime import sha


class BitsRecognizer:
    def __init__(self, *, public_root, keys, vectors, gate, gate_sha256, runtime, runtime_factory=None):
        from projects.algorithm_solver.catalogue.boundary_policy import validate_policy
        self.public_root = Path(public_root).resolve()
        self.bits = self.public_root/'labs/two-button'
        self.runtime = runtime
        self.runtime_factory = runtime_factory
        self.lock = threading.Lock()
        for path, limit in ((keys, 2*1024**2), (vectors, 64*1024**2), (gate, 1024**2)):
            if Path(path).stat().st_size > limit:
                raise ValueError('recognition input exceeds bound')
        if sha(gate) != gate_sha256:
            raise ValueError('source boundary gate changed')
        self.gate = json.loads(Path(gate).read_text())
        raw = {}
        for name, path in self.gate['artifact_paths'].items():
            if Path(path).stat().st_size > 8*1024**2:
                raise ValueError('boundary metadata exceeds bound')
            raw[name] = Path(path).read_bytes()
        self.policy = validate_policy(raw, self.gate['trusted_hashes'])
        self.aliases = json.loads(raw['identity_aliases'])['by_key']
        self.keys = json.loads(Path(keys).read_text())
        self.vectors = np.load(vectors, allow_pickle=False, mmap_mode='r')
        if (type(self.keys) is not list or len(set(self.keys)) != len(self.keys)
                or self.vectors.shape != (len(self.keys), 1024)
                or self.vectors.dtype != np.float32 or not np.isfinite(self.vectors).all()
                or not np.allclose(np.linalg.norm(self.vectors, axis=1), 1, atol=1e-4)):
            raise ValueError('invalid known-corpus vector identity or shape')
        catalogue_path = self.bits/'challenges.json'
        manifest_path = self.bits/'problems/manifest.json'
        catalogue = json.loads(catalogue_path.read_text())
        self.manifest = json.loads(manifest_path.read_text())
        self.metadata = {}
        for row in catalogue['problems']:
            slug, title = row['slug'], row['title']
            key = 'lc:'+slug
            if not re.fullmatch('[a-z0-9-]+', slug) or not isinstance(title, str) or not title:
                raise ValueError('invalid published problem metadata')
            self.metadata[key] = {'key': key, 'slug': slug, 'title': title,
                                  'problem_id': self.aliases.get(key),
                                  'difficulty': row.get('difficulty', 'Unknown')}
        if set(self.keys) != set(self.metadata) or any(key not in self.aliases for key in self.keys):
            raise ValueError('published catalogue, aliases and vector keys disagree')
        self.identity = {'schema': 'gamma.bits-discovery-index.v1',
                         'keys_sha256': sha(keys), 'vectors_sha256': sha(vectors),
                         'catalogue_sha256': sha(catalogue_path), 'packets_sha256': sha(manifest_path),
                         'gate_sha256': gate_sha256, 'runtime': runtime.identity,
                         'document_vectors': 'Existing frozen Qwen reference vectors; Doppler query embeddings.',
                         'recognition_qualified': False}
        self.identity_sha256 = hashlib.sha256(json.dumps(self.identity, sort_keys=True).encode()).hexdigest()

    def document(self, key):
        """Only open a published statement after current source-boundary approval."""
        from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open
        row = self.metadata[key]
        try:
            authorize_before_open(row['problem_id'], self.gate['artifact_paths'],
                                  self.gate['trusted_hashes'], language='python', payload_kind='statement')
        except PermissionError:
            return row['title'], 'title-only'
        path = self.bits/'problems'/f"{row['slug']}.json"
        if path.stat().st_size > 1024**2:
            raise ValueError('statement packet exceeds bound')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != self.manifest['problems'][row['slug']]['sha256']:
            raise ValueError('published statement packet changed')
        packet = json.loads(raw)
        if packet['problem']['slug'] != row['slug'] or not isinstance(packet['problem']['statement'], str):
            raise ValueError('published statement identity mismatch')
        # Public examples, starter signatures and all other fields are not returned.
        return packet['problem']['statement'], 'published-statement'

    def recognize(self, text):
        if type(text) is not str or not text.strip() or len(text.encode()) > 32768:
            raise ValueError('Enter a problem description of at most 32 KB.')
        query = text.strip()
        base = {'schema': 'gamma.bits-recognition.v1', 'query_sha256': hashlib.sha256(text.encode()).hexdigest(),
                'index_sha256': self.identity_sha256, 'recognition_qualified': False}
        normalized = query.casefold()
        exact = [row for row in self.metadata.values() if normalized in
                 (row['title'].casefold(), row['slug'], str(row['problem_id']),
                  '#'+str(row['problem_id']).removeprefix('leetcode:'))]
        if len(exact) == 1:
            return dict(base, status='candidates', method='exact-metadata', candidates=exact)
        if not self.lock.acquire(blocking=False):
            raise RuntimeError('Recognition is busy. Try again.')
        try:
            if getattr(self.runtime, '_closed', False) and self.runtime_factory:
                successor = self.runtime_factory()
                if successor.identity != self.identity['runtime']:
                    successor.close()
                    raise RuntimeError('Recognition runtime changed; restart the local server.')
                self.runtime = successor
            vector = self.runtime.encode([query], query=True)[0]
            if self.runtime.last_receipt['embedding_rows'][0].get('truncated'):
                return dict(base, status='abstain', reason='query_too_long', candidates=[])
            similarities = self.vectors @ vector
            # Availability never filters recognition. Original vector positions are retained.
            positions = sorted(range(len(self.keys)), key=lambda i: (-float(similarities[i]), self.keys[i]))[:10]
            keys = [self.keys[i] for i in positions]
            descriptions = [self.document(key) for key in keys]
            evidence = self.runtime.rerank_evidence(query, [text for text, _ in descriptions])
            scores = [row['trueLogit'] - row['falseLogit'] for row in evidence]
            order = sorted(range(len(keys)), key=lambda i: (-scores[i], keys[i]))[:3]
            candidates = [dict(self.metadata[keys[i]], document_scope=descriptions[i][1]) for i in order]
            return dict(base, status='candidates', method='embedding-and-reranking', candidates=candidates)
        finally:
            self.lock.release()

    def close(self):
        self.runtime.close()
