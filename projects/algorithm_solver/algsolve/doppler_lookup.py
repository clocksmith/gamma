"""Doppler recognition candidate; separate index/calibration from the CPU control.

build: resume a source-bound index using the retained embedding model.
query: JSONL Problem inputs -> stored answer or abstention; no generation/dialogue.
Without a development calibration, return ranked candidates but never approve code.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time

import numpy as np

from .approved_library import ApprovedLibrary, digest
from .doppler_runtime import DopplerRuntime, sha
from .lookup import LookupIndex
from .records import LANE_ROOT, Problem
from .splits import IndexEntry


def embedding_identity(runtime):
    # Reranker changes cannot silently change the document embedding space.
    return {k: v for k, v in runtime.identity.items() if k != 'models'} | {
        'model': runtime.identity['models']['embedding']}


def build_index(runtime, entries_path, catalog_path, output, *, reference_vectors=None, reference_keys=None):
    catalog = ApprovedLibrary.load(catalog_path)
    source_entries = [IndexEntry(**json.loads(line)) for line in entries_path.read_text().splitlines() if line.strip()]
    allowed = [i for i, e in enumerate(source_entries)
               if catalog.manifest['excluded'].get(e.key) != 'protected_composition_alias']
    entries = [source_entries[i] for i in allowed]
    if len({e.key for e in entries}) != len(entries):
        raise ValueError('Duplicate corpus keys')
    contract = {'schema': 'algsolve.doppler-index.v1', 'embedding': embedding_identity(runtime),
                'source_sha256': sha(entries_path), 'catalog_sha256': sha(catalog_path),
                'keys': [e.key for e in entries]}
    reference = None
    if (reference_vectors is None) != (reference_keys is None):
        raise ValueError('Reference vectors require their ordered keys')
    if reference_vectors is not None:
        # Reuse the immutable, qualified Qwen reference space, explicitly. Query
        # embeddings still execute in Doppler; calibration tests this mixed pair.
        pins = catalog.manifest['runtime_files_sha256']
        for name, path in [('corpus_entries.jsonl', entries_path),
                           ('corpus_embeddings.npy', reference_vectors),
                           ('corpus_embedding_keys.json', reference_keys)]:
            if pins.get('data/derived/'+name) != sha(path):
                raise ValueError('Reference index differs from source catalog: '+name)
        keys = json.loads(reference_keys.read_text())
        if keys != [e.key for e in source_entries]:
            raise ValueError('Reference vector key order differs')
        reference = np.load(reference_vectors, allow_pickle=False)[allowed]
        if reference.shape != (len(entries), 1024) or not np.isfinite(reference).all():
            raise ValueError('Invalid reference embedding matrix')
        from .embed import EXPECTED_SHA256
        contract['document_embedding'] = {
            'runtime': 'cached-transformers-qwen3-embedding-0.6b',
            'weights': EXPECTED_SHA256, 'vectors_sha256': sha(reference_vectors),
            'keys_sha256': sha(reference_keys),
            'scope': 'Cached reference documents + Doppler queries; independently calibrated candidate',
        }
    else:
        contract['document_embedding'] = {'runtime': 'doppler', 'identity': embedding_identity(runtime)}
    output.mkdir(parents=True, exist_ok=True)
    contract_path = output/'contract.json'
    if contract_path.exists():
        if json.loads(contract_path.read_text()) != contract:
            raise ValueError('Index inputs/runtime changed; use a new output directory')
    else:
        contract_path.write_text(json.dumps(contract, indent=2) + '\n')
        (output/'entries.jsonl').write_text(''.join(json.dumps(asdict(e)) + '\n' for e in entries))
    if (output/'entries.jsonl').read_text() != ''.join(json.dumps(asdict(e)) + '\n' for e in entries):
        raise ValueError('Index entry snapshot changed')
    rows_path = output/'vectors.jsonl'
    rows = read_vectors(rows_path, contract['keys']) if rows_path.exists() else []
    with rows_path.open('a') as stream:
        for index, entry in list(enumerate(entries))[len(rows):]:
            start = time.monotonic()
            vector = runtime.encode([entry.query_text()])[0] if reference is None else reference[index]
            row = {'key': entry.key, 'embedding': vector.tolist(),
                   'seconds': time.monotonic()-start,
                   'receipt': runtime.last_receipt if reference is None else {'cached_reference': True}}
            stream.write(json.dumps(row, allow_nan=False) + '\n')
            stream.flush()
            rows.append(row)
            if len(rows) % 25 == 0 or len(rows) == len(entries):
                print(json.dumps({'indexed': len(rows), 'total': len(entries)}), flush=True)
    manifest = {'contract_sha256': sha(contract_path), 'entries_sha256': sha(output/'entries.jsonl'),
                'vectors_sha256': sha(rows_path), 'count': len(rows)}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def read_vectors(path, keys):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if [r['key'] for r in rows] != keys[:len(rows)] or len(rows) > len(keys):
        raise ValueError('Index vector order changed')
    for row in rows:
        vector = np.asarray(row['embedding'], dtype=np.float32)
        if vector.shape != (1024,) or not np.isfinite(vector).all() or not np.isclose(np.linalg.norm(vector), 1, atol=1e-4):
            raise ValueError('Invalid index vector')
    return rows


class DopplerLookup:
    def __init__(self, runtime, directory, *, catalog=None, calibration=None, rerank=False):
        self.runtime, self.rerank, self.catalog = runtime, rerank, catalog
        directory = Path(directory)
        manifest = json.loads((directory/'manifest.json').read_text())
        for name in ('contract', 'entries', 'vectors'):
            path = directory / (name + ('.json' if name == 'contract' else '.jsonl'))
            if sha(path) != manifest[name + '_sha256']:
                raise ValueError('Doppler index artifact changed: ' + name)
        contract = json.loads((directory/'contract.json').read_text())
        if contract['embedding'] != embedding_identity(runtime):
            raise ValueError('Query encoder differs from index encoder')
        entries = [IndexEntry(**json.loads(line)) for line in (directory/'entries.jsonl').read_text().splitlines()]
        rows = read_vectors(directory/'vectors.jsonl', contract['keys'])
        if len(rows) != len(entries) or len(rows) != manifest['count']:
            raise ValueError('Incomplete Doppler index')
        if [e.key for e in entries] != contract['keys']:
            raise ValueError('Index entries differ from contract')
        self.index = LookupIndex(entries, np.array([r['embedding'] for r in rows], dtype=np.float32))
        self.identity = {'index': digest(manifest), 'runtime': runtime.identity, 'rerank': rerank,
                         'adapter_sha256': sha(Path(__file__).with_name('doppler_runtime.py')),
                         'lookup_sha256': sha(__file__),
                         'recognition_sha256': {
                             name: sha(LANE_ROOT/'algsolve'/name) for name in
                             ('answer.py', 'lookup.py', 'interface_compatibility.py', 'approved_library.py')}}
        self.thresholds = None
        if calibration is not None:
            from .rerank_recognition import calibrate
            calibration = json.loads(Path(calibration).read_text())
            if calibration.get('identity') != self.identity or calibration.get('partition') != 'development':
                raise ValueError('Calibration does not bind this development candidate')
            rows = calibration['development_rows']
            if (calibration['development_evidence_sha256'] != digest(rows)
                    or calibration['thresholds'] != calibrate(rows, calibration['expected_queries'])):
                raise ValueError('Calibration differs from its development evidence')
            thresholds = calibration['thresholds']
            if any(type(thresholds.get(k)) not in (int, float) or not np.isfinite(thresholds[k])
                   for k in ('min_score', 'min_margin')) or thresholds['min_margin'] < 0:
                raise ValueError('Invalid thresholds')
            self.thresholds = thresholds

    def rank(self, query):
        started = time.monotonic()
        vector = self.runtime.encode([query.statement], query=True)[0]
        candidates = self.index.scored_candidates(query.statement, vector)
        embedding_ms = (time.monotonic()-started) * 1000
        rerank_ms = 0.
        if self.rerank:
            started_rerank = time.monotonic()
            scores = self.runtime.rerank(query.statement, [
                self.index.entries[self.index.by_key[c['key']]].query_text() for c in candidates])
            candidates = sorted([dict(c, score=s) for c, s in zip(candidates, scores)],
                                key=lambda c: (-c['score'], c['key']))
            rerank_ms = (time.monotonic()-started_rerank) * 1000
        return candidates, {'embedding_lookup_ms': embedding_ms, 'rerank_ms': rerank_ms,
                            'total_ms': (time.monotonic()-started)*1000}

    def recognize(self, query):
        from .answer import answer
        from .routes import Budget, Context
        start = time.monotonic()
        if self.thresholds is None:
            # Uncalibrated scores are inspection evidence, not answer authority.
            candidates, timing = self.rank(query)
            return {'decision': 'abstain', 'reason': 'doppler_calibration_required', 'code': None,
                    'candidates': candidates, 'recognition_qualified': False,
                    'seconds': time.monotonic()-start, 'timing': timing}
        if self.catalog is None:
            raise ValueError('Returning stored code requires an approved source catalog')
        budget = Budget.from_contract(json.loads((LANE_ROOT/'contracts/run_contract.json').read_text()))
        context = Context(generator=None, embedder=self.runtime, lookup=self.index,
                          thresholds=self.thresholds, classifier=None, entries=self.index.entries, budget=budget)
        context.statement_thresholds = self.thresholds
        result = answer(context, query, approved_library=self.catalog,
                        reranker=(lambda _, documents: self.runtime.rerank(query.statement, documents))
                        if self.rerank else None,
                        rerank_thresholds=self.thresholds if self.rerank else None)
        # Catalog.check verifies stored source; this is a new recognition candidate,
        # not the historical CPU serving qualification or a protected result.
        return dict(result, recognition_qualified=False, recognition_runtime='doppler')


def calibrate_development(lookup, path, output):
    """Use consumed development descriptions only; historical 'clarify' -> abstain."""
    from .rerank_recognition import calibrate
    from .lookup import decide
    source = json.loads(path.read_text())
    if source.get('partition') != 'development':
        raise ValueError('Calibration requires explicitly identified development data')
    cases = source['cases']
    if not cases or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Development cases must be nonempty and unique')
    expected = []
    for case in cases:
        label = case['expected']
        if label['action'] not in ('match', 'abstain', 'clarify'):
            raise ValueError('Unknown development label')
        target = label['keys'][0] if label['action'] == 'match' and len(label['keys']) == 1 else None
        if label['action'] == 'match' and target is None:
            raise ValueError('Calibration requires a unique intended identity')
        if target is not None and target not in lookup.index.by_key:
            raise ValueError('Development target is absent or protected')
        expected.append({'qid': case['id'], 'target': target})
    contract = {'identity': lookup.identity, 'development_source_sha256': sha(path),
                'expected_queries': expected, 'partition': 'development',
                'label_policy': 'Historical clarify means abstain; no questions',
                'scope': 'Pre-public-check recognition calibration, not answer/release qualification'}
    output.mkdir(parents=True, exist_ok=True)
    contract_path = output/'contract.json'
    if contract_path.exists() and json.loads(contract_path.read_text()) != contract:
        raise ValueError('Calibration identity changed; use a new output directory')
    contract_path.write_text(json.dumps(contract, indent=2)+'\n')
    rows_path = output/'development.jsonl'
    rows = [json.loads(line) for line in rows_path.read_text().splitlines()] if rows_path.exists() else []
    if [r['qid'] for r in rows] != [c['id'] for c in cases[:len(rows)]] or len(rows) > len(cases):
        raise ValueError('Development receipt order changed')
    with rows_path.open('a') as stream:
        for case, label in list(zip(cases, expected))[len(rows):]:
            query = Problem(uid='dev:'+case['id'], source='development', source_id=case['id'],
                            title='', slug='', statement=case['query'], io_mode='functional')
            candidates, timing = lookup.rank(query)
            row = dict(label, reranked=candidates, timing=timing, kind=case['kind'])
            stream.write(json.dumps(row, allow_nan=False)+'\n')
            stream.flush()
            rows.append(row)
            print(json.dumps({'development': len(rows), 'total': len(cases)}), flush=True)
    thresholds = calibrate(rows, expected)
    calibration = dict(contract, thresholds=thresholds, development_rows=rows,
                       development_evidence_sha256=digest(rows))
    (output/'calibration.json').write_text(json.dumps(calibration, indent=2, allow_nan=False)+'\n')
    decisions = [decide(r['reranked'], thresholds).key for r in rows]
    summary = {
        'scope': contract['scope'], 'cases': len(rows),
        'correct_accepted': sum(k is not None and k == r['target'] for k, r in zip(decisions, rows)),
        'wrong_accepted': sum(k is not None and k != r['target'] for k, r in zip(decisions, rows)),
        'abstained': sum(k is None for k in decisions),
        'top1_correct_known': sum(r['target'] is not None and r['reranked'][0]['key'] == r['target'] for r in rows),
        'median_total_ms': float(np.median([r['timing']['total_ms'] for r in rows])),
        'first_query_ms': rows[0]['timing']['total_ms'],
        'thresholds': thresholds,
    }
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('build', 'query', 'calibrate'))
    parser.add_argument('--doppler-root', type=Path, required=True)
    parser.add_argument('--embedding-model', type=Path, required=True)
    parser.add_argument('--reranker-model', type=Path)
    parser.add_argument('--surface', choices=('node', 'browser'), default='node')
    parser.add_argument('--rerank', action='store_true', help='Enable scoring, separately calibrated')
    parser.add_argument('--runtime-config', type=Path, help='Explicit per-role runtime configs: embedding/rerank')
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--entries', type=Path)
    parser.add_argument('--reference-vectors', type=Path, help='Explicitly reuse pinned reference document vectors')
    parser.add_argument('--reference-keys', type=Path)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--calibration', type=Path)
    parser.add_argument('--development', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--queries', type=Path, help='JSONL Problem inputs; omit to retain models over stdin')
    args = parser.parse_args()
    if args.operation == 'build' and (not args.entries or not args.catalog):
        parser.error('build requires --entries and --catalog')
    if args.operation == 'calibrate' and (not args.development or not args.output):
        parser.error('calibrate requires --development and --output')
    if args.rerank and not args.reranker_model:
        parser.error('--rerank requires --reranker-model')
    configs = json.loads(args.runtime_config.read_text()) if args.runtime_config else {}
    with DopplerRuntime(args.doppler_root, args.embedding_model, args.reranker_model,
                        embedding_config=configs.get('embedding'), reranker_config=configs.get('rerank'),
                        surface=args.surface) as runtime:
        if args.operation == 'build':
            print(json.dumps(build_index(runtime, args.entries, args.catalog, args.index,
                                         reference_vectors=args.reference_vectors,
                                         reference_keys=args.reference_keys)))
        else:
            import sys
            catalog = ApprovedLibrary.load(args.catalog) if args.catalog else None
            lookup = DopplerLookup(runtime, args.index, catalog=catalog,
                                   calibration=args.calibration, rerank=args.rerank)
            if args.operation == 'calibrate':
                print(json.dumps(calibrate_development(lookup, args.development, args.output)))
                return
            source = args.queries.open() if args.queries else sys.stdin
            try:
                for line in source:
                    if line.strip():
                        print(json.dumps(lookup.recognize(Problem.from_dict(json.loads(line))),
                                         allow_nan=False), flush=True)
            finally:
                if args.queries:
                    source.close()


if __name__ == '__main__':
    main()
