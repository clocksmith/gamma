"""Development calibration with oracle signatures removed from query inputs.

Uses only the old, already-inspected recognition sets. Protected composition
aliases are removed. Controlled absent queries remove a complete sibling family;
this is development calibration, not naturally absent-problem evidence.
"""
import argparse
import json
from pathlib import Path
import time

from . import corpus, paraphrase, splits
from .library_audit import inputs, sha, write
from .lookup import LookupIndex
from .records import LANE_ROOT
from .rerank_recognition import calibrate, diagnostic_entries
from .interface_compatibility import filter_candidates
from .public_examples import recover


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if not args.name.replace('-', '').isalnum():
        raise ValueError('Invalid run name')
    import numpy as np
    import torch
    from .embed import Embedder
    torch.set_num_threads(4)
    raw, entries, problems, boundary = inputs()
    keys = json.loads(corpus.KEYS_PATH.read_text())
    if keys != [r['key'] for r in raw]:
        raise ValueError('Index order differs')
    blocked = set(boundary['keys'])
    vectors = np.load(corpus.EMBEDDINGS_PATH)[[i for i,k in enumerate(keys) if k not in blocked]]
    index = LookupIndex(entries, vectors)
    by_key = {e.key:e for e in entries}
    paragraphs = {r['key']:r for r in map(json.loads, paraphrase.PARAPHRASES_PATH.read_text().splitlines())}
    manifest = splits.load_manifest()
    proposed = manifest['recognition_dev'] + [q for q in manifest['recognition'] if q['kind'] != 'absent_exact']
    queries = [q for q in proposed if (q['target'] in by_key if q['kind'] != 'absent_exact'
                                      else q['problem_uid'] in problems)]
    files = [corpus.ENTRIES_PATH, corpus.EMBEDDINGS_PATH, corpus.KEYS_PATH, paraphrase.PARAPHRASES_PATH,
             LANE_ROOT / 'contracts/sample_manifest.json', Path(__file__),
             LANE_ROOT / 'algsolve/lookup.py', LANE_ROOT / 'algsolve/embed.py',
             LANE_ROOT / 'algsolve/interface_compatibility.py']
    contract = {'scope': 'old inspected recognition queries now development-only; no fresh cases',
                'query_count': len(queries), 'excluded_count': len(proposed)-len(queries),
                'input_sha256': {str(p.relative_to(LANE_ROOT)):sha(p) for p in files},
                'query_input': 'statement only; no oracle method, parameters, title or slug',
                'device': 'cpu', 'generation': False,
                'absent_policy': 'remove complete canonical sibling family; controlled absence only'}
    directory = LANE_ROOT / 'runs' / args.name
    directory.mkdir(exist_ok=True, parents=True)
    if (directory/'contract.json').exists() and json.loads((directory/'contract.json').read_text()) != contract:
        raise ValueError('Calibration resume contract changed')
    write(directory/'contract.json', contract)
    output = directory/'queries.jsonl'
    rows = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
    done = {r['qid'] for r in rows}
    if len(done) != len(rows) or not done <= {q['qid'] for q in queries}:
        raise ValueError('Invalid resumed rows')
    encoder = Embedder(device='cpu')
    with output.open('a') as stream:
        for q in queries:
            if q['qid'] in done:
                continue
            if q['kind'] == 'exact':
                text = by_key[q['target']].statement
            elif q['kind'] == 'absent_exact':
                text = problems[q['problem_uid']].statement
            else:
                text = paragraphs[q['target']]['paraphrase']
            indices = diagnostic_entries(entries, q, problems)
            active = LookupIndex([entries[i] for i in indices], vectors[indices]) if q['kind']=='absent_exact' else index
            started = time.perf_counter()
            candidates = active.scored_candidates(text, encoder.encode([text], query=True)[0])
            source = problems.get(q.get('problem_uid'))
            if source is None and q.get('target') in by_key:
                source = next((problems[uid] for uid in by_key[q['target']].members if uid in problems), None)
            examples = recover(source).public_tests if source else []
            candidates, rejected = filter_candidates(candidates, active, examples)
            row = {'qid':q['qid'], 'target':q['target'], 'kind':q['kind'],
                   'reranked':candidates, 'interface_rejections':rejected,
                   'seconds':time.perf_counter()-started}
            rows.append(row); stream.write(json.dumps(row)+'\n'); stream.flush()
            print(f'[statement-calibration] {len(rows)}/{len(queries)}', flush=True)
    supported = [dict(r, reranked=r['reranked'] if len(r['reranked'])>1 else
                      r['reranked']+[{'key':None,'score':-1.}]) for r in rows if r['reranked']]
    qids = {r['qid'] for r in supported}
    thresholds = calibrate(supported, [q for q in queries if q['qid'] in qids])
    thresholds['incompatible_queries_abstained'] = len(rows)-len(supported)
    thresholds['fitted_on'] = 'old inspected recognition development and known-query diagnostics, statement only'
    write(directory/'thresholds.json', thresholds)
    print(json.dumps(thresholds), flush=True)


if __name__ == '__main__':
    main()
