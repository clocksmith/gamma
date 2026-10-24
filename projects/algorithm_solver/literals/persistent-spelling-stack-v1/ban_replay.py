"""Independent old-parser batching for already sealed reporter inputs only.

This is never imported by scientific execution. It changes neither encounter
order nor ban authority: each cached set comes from the unchanged structure
helper on exactly the hash-bound source, before replay consumes it.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import time


class BanReplay:
    def __init__(self, helper, deadline, timeout_error=TimeoutError):
        self.helper = Path(helper)
        self.deadline = deadline
        self.timeout_error = timeout_error
        self.entries = {}
        self.bodies = {}
        self.batches = 0
        self.parsed_variants = 0
        self.seconds = 0.0

    @staticmethod
    def source_hash(text):
        return hashlib.sha256(text.encode()).hexdigest()

    def extend(self, variants):
        pending = {}
        for key, text in variants.items():
            assert type(key) is str and type(text) is str
            assert key.rsplit(':', 1)[-1] == self.source_hash(text)
            if key in self.entries:
                assert self.entries[key][0] == text
            else:
                pending[key] = text
        ordered = sorted(pending)
        for offset in range(0, len(ordered), 16):
            chunk = {key: pending[key] for key in ordered[offset:offset + 16]}
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise self.timeout_error('Independent ban replay deadline')
            started = time.monotonic()
            completed = subprocess.run(['/usr/bin/node', str(self.helper)],
                input=json.dumps(chunk), text=True, capture_output=True,
                check=True, timeout=remaining)
            parsed = json.loads(completed.stdout)
            assert type(parsed) is dict and parsed.keys() == chunk.keys()
            checked = {}
            for key, text in chunk.items():
                row = parsed[key]
                assert type(row) is dict and set(row) == {'labels', 'bodies'}
                assert type(row['labels']) is list and len(row['labels']) == len(text)
                assert type(row['bodies']) is list and row['bodies']
                assert all(type(body) is str and body for body in row['bodies'])
                checked[key] = (text, frozenset([text, *row['bodies']]))
            self.entries.update(checked)
            self.bodies.update({key: parsed[key]['bodies'] for key in chunk})
            self.batches += 1
            self.parsed_variants += len(chunk)
            self.seconds += time.monotonic() - started

    def banned(self, texts):
        result = set()
        for key, text in texts.items():
            # Reporter ledger uses PID:hash; global unions use that same key.
            assert key in self.entries, 'Replay requested an unrecorded variant'
            source, bans = self.entries[key]
            assert source == text and key.rsplit(':', 1)[-1] == self.source_hash(text)
            result.update(bans)
        return result

    def receipt(self):
        return {'authority': 'unchanged tail-search-v1/structure.cjs plus lexical.cjs',
                'scope': 'report-only, sealed phase variants; exact key/hash/text binding',
                'batch_size': 16, 'batches': self.batches,
                'parsed_variants': self.parsed_variants, 'parser_seconds': self.seconds,
                'execution_cache': False, 'persistent_parser_used': False}
