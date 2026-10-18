"""Disposable bridge jobs. No hidden-test loading, downloads, or generation."""
import contextlib
import json
import signal
import sys
from .editor_execution import execute, query_problem
from .public_examples import recover
from .records import Problem


def details(slug):
    from . import corpus, splits
    entry = next((e for e in corpus.read_entries() if e.slug == slug), None)
    if entry is None:
        raise ValueError('Unknown challenge')
    problems = splits.load_all()
    originals = [problems[uid] for uid in entry.members if uid in problems]
    original = next((p for p in originals if p.public_tests and p.io_mode == 'functional'), None)
    query = Problem(uid='user:editor', source='user', source_id=slug, title=entry.title,
                    slug=slug, statement=entry.statement, io_mode='functional', entry=entry.entry,
                    params=entry.params, starter_code=entry.starter_code,
                    public_tests=original.public_tests if original else [])
    query = recover(query)
    normalized = query_problem(json.loads(query.to_json()))
    names = ', '.join(p[0] for p in entry.params)
    normalized.starter_code = f"class {normalized.entry.get('class') or 'Solution'}:\n    def {normalized.entry['method']}(self{', ' if names else ''}{names}):\n        pass\n"
    return {'problem': json.loads(normalized.to_json()),
            'starters': {'python': normalized.starter_code,
                         'javascript': f"function {entry.entry['method']}({names}) {{\n    // Your solution\n}}\n"},
            'source': {'attribution': entry.attribution, 'license': entry.license,
                       'use': 'Authenticated personal research view; not a public republication license',
                       'export_scope': 'statement, starter signatures and public examples only'},
            'example_passed': None, 'independent_tests_passed': None}


def retrieve(raw, approved_library=None):
    if approved_library is not None:
        from .approved_library import load_context
        from .answer import answer
        context, catalog = load_context(approved_library)
        return dict(answer(context, query_problem(raw), approved_library=catalog), language='python')
    import numpy as np
    import torch
    from . import corpus
    from .answer import answer
    from .embed import Embedder
    from .lookup import LookupIndex, load_thresholds
    from .records import LANE_ROOT
    from .routes import Budget, Context
    torch.set_num_threads(4)
    entries = corpus.read_entries()
    if json.loads(corpus.KEYS_PATH.read_text()) != [e.key for e in entries]:
        raise ValueError('Corpus embeddings out of sync')
    contract = json.loads((LANE_ROOT / 'contracts/run_contract.json').read_text())
    context = Context(generator=None, embedder=Embedder(device='cpu'),
                      lookup=LookupIndex(entries, np.load(corpus.EMBEDDINGS_PATH)),
                      thresholds=load_thresholds(), classifier=None, entries=entries,
                      budget=Budget.from_contract(contract))
    return dict(answer(context, query_problem(raw)), language='python')


def run_job(payload, connection, request_digest, approved_library=None):
    def stop(*_):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    try:
        with contextlib.redirect_stdout(sys.stderr):
            if payload['operation'] == 'challenge':
                result = details(payload.get('slug'))
            elif payload['operation'] == 'run':
                result = execute(payload.get('language'), payload.get('source'), payload.get('problem'))
            elif payload['operation'] == 'retrieve':
                result = retrieve(payload.get('problem'), approved_library=approved_library)
            else:
                raise ValueError('Unknown operation')
        result['request_binding'] = {'request_sha256': request_digest}
        if len(json.dumps(result).encode()) > 262144:
            raise ValueError('Result exceeds bridge size limit')
        connection.send({'state': 'complete', 'result': result})
    except Exception as error:
        connection.send({'state': 'failed', 'error': type(error).__name__ + ': ' + str(error)[:500]})
    finally:
        connection.close()
