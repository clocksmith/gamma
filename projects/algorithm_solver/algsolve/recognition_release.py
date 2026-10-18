"""One frozen opening of the independent 1a subset; no tuning or repair."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import time

from .approved_library import load_context
from .answer import answer
from .library_audit import sha, write
from .records import LANE_ROOT, Problem

SUBSET_SHA = '930da2fdd5fad21dc3942d419d85bd699c2f8dcc3082f768fa15919891d70649'


def public_problem(case):
    # Deliberately no oracle signature/requirements/identity. The source chosen
    # by the candidate supplies its interface for positional public examples.
    return Problem(uid='user:recognition', source='user', source_id='recognition',
                   title='', slug='', statement=case['query'], io_mode='functional',
                   public_tests=case['public_examples'])


def freeze(directory, catalog, queries):
    from . import corpus
    from .embed import EXPECTED_SHA256, verify_weights
    if sha(queries) != SUBSET_SHA:
        raise ValueError('Independent subset seal differs')
    verify_weights()
    files = sorted((LANE_ROOT/'algsolve').rglob('*.py')) + [
        corpus.ENTRIES_PATH, corpus.KEYS_PATH, corpus.EMBEDDINGS_PATH, catalog, queries,
        LANE_ROOT/'contracts/lookup_thresholds.json', LANE_ROOT/'contracts/statement_lookup_thresholds.json',
        LANE_ROOT/'contracts/known_lookup_release_v1.json']
    bound = {str(p.absolute().relative_to(LANE_ROOT.absolute())):sha(p) for p in files}
    contract = {'schema':'algsolve.known-lookup-candidate.v1', 'files_sha256':bound,
                'catalog':str(catalog.resolve().relative_to(LANE_ROOT.resolve())),
                'queries':str(queries.resolve().relative_to(LANE_ROOT.resolve())),
                'embedding_sha256':EXPECTED_SHA256, 'platform':platform.platform(),
                'python':platform.python_version(), 'device':'cpu', 'threads':4,
                'input':'query text and public positional examples only; oracle signature excluded',
                'no_tuning':'one opening, frozen candidate, no retries or repair',
                'scope':'agent-authored/reviewed known-query and naturally absent sample; not human evidence'}
    directory.mkdir(parents=True, exist_ok=False)
    write(directory/'contract.json', contract)
    return contract


def score(directory):
    from . import validate
    from .recognition_metrics import summarize_results
    contract = json.loads((directory/'contract.json').read_text())
    for relative, expected in contract['files_sha256'].items():
        if sha(LANE_ROOT/relative) != expected:
            raise ValueError('Frozen candidate changed: '+relative)
    if platform.platform() != contract['platform'] or platform.python_version() != contract['python']:
        raise ValueError('Candidate environment changed')
    started = time.perf_counter()
    context, approved = load_context(LANE_ROOT/contract['catalog'])
    exact_ready = time.perf_counter()-started
    context.embedder.encode(['Find an indexed programming problem.'], query=True)
    write(directory/'opening.json', {'context_ready_seconds':exact_ready,
          'encoder_ready_seconds':time.perf_counter()-started, 'os_caches_flushed':False,
          'scope':'fresh context and encoder plus neutral warmup; Python process imports excluded',
          'host_exclusive':False, 'runtime':{'python':platform.python_version(), 'platform':platform.platform()}})
    cases = json.loads((LANE_ROOT/contract['queries']).read_text())['cases']
    kinds = [c['kind'] for c in cases]
    if len(cases)!=24 or any(kinds.count(k)!=n for k,n in
                            [('paraphrase',12),('sibling_variant',8),('absent_algorithm',4)]):
        raise ValueError('Subset counts differ from acceptance contract')
    responses_path = directory/'responses.jsonl'
    responses = {r['id']:r['response'] for r in map(json.loads,responses_path.read_text().splitlines())} if responses_path.exists() else {}
    output = directory/'scores.jsonl'
    rows = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
    done = {r['id'] for r in rows}
    if len(done)!=len(rows) or not done <= {c['id'] for c in cases}:
        raise ValueError('Invalid resumed scoring')
    for case in cases:
        if case['id'] in done:
            continue
        result = responses.get(case['id'])
        if result is None:
            result = answer(context, public_problem(case), approved_library=approved)
            # Capture the complete candidate response BEFORE accessing private checks.
            with responses_path.open('a') as stream:
                stream.write(json.dumps({'id':case['id'], 'response':result})+'\n')
        accepted = result['decision']=='answered'
        identity = (result.get('match') or {}).get('key')
        correct_identity = case['expected_key'] is not None and identity==case['expected_key']
        verdict = None
        if accepted and result.get('code') and case['private_checks']:
            oracle_query = public_problem(case)
            oracle_query.entry = result['answer_interface']
            verdict = validate.judge_problem(oracle_query, result['code'], case['private_checks'], wall_seconds=30).to_dict()
        passed = bool(verdict and verdict['passed'] and verdict['tests_passed']>0)
        candidates = (result.get('match') or {}).get('candidates', [])
        row = {'id':case['id'], 'family':case['family'], 'kind':case['kind'], 'difficulty':case['difficulty'],
               'expected_key':case['expected_key'], 'accepted':accepted, 'identity_correct':correct_identity,
               'accepted_and_correct':accepted and correct_identity and passed,
               'wrong_acceptance':accepted and (not correct_identity or bool(verdict and not verdict['passed'])),
               'accepted_unqualified':accepted and verdict is None,
               'top_five':case['expected_key'] in [c['key'] for c in candidates[:5]],
               'retrieval_executed':bool(candidates), 'questions':0, 'independent':verdict,
               'result':{k:v for k,v in result.items() if k!='code'},
               'code_sha256':hashlib.sha256(result['code'].encode()).hexdigest() if result.get('code') else None}
        with output.open('a') as stream:
            stream.write(json.dumps(row)+'\n')
        rows.append(row)
        print(f'[recognition-release] {len(rows)}/24 {result["decision"]}', flush=True)
    known = [r for r in rows if r['kind']!='absent_algorithm']
    absent = [r for r in rows if r['kind']=='absent_algorithm']
    gate = {'known_correct':sum(r['accepted_and_correct'] for r in known),
            'wrong_acceptances':sum(r['wrong_acceptance'] for r in rows),
            'accepted_unqualified':sum(r['accepted_unqualified'] for r in rows),
            'absent_rejected':sum(not r['accepted'] for r in absent)}
    gate['passed'] = (gate['known_correct']>=18 and gate['wrong_acceptances']==0
                      and gate['accepted_unqualified']==0 and gate['absent_rejected']==4)
    summary = {'gate':gate, 'metrics':summarize_results(rows), 'known':summarize_results(known),
               'absent':summarize_results(absent), 'contract_sha256':sha(directory/'contract.json'),
               'limits': ['Small purposive agent-authored/reviewed sample; not human evidence.',
                          'Finite checks do not prove correctness. Wrong identity is scored independently.',
                          'No tuning after opening; a failed gate remains failed.',
                          'The other 16 description cases and composition targets remain sealed.']}
    write(directory/'summary.json', summary)
    return gate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze','score'))
    parser.add_argument('--name', required=True)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--queries', type=Path)
    args = parser.parse_args()
    if not args.name.replace('-','').isalnum():
        raise ValueError('Invalid name')
    directory = LANE_ROOT/'runs'/args.name
    if args.action=='freeze' and (not args.catalog or not args.queries):
        parser.error('freeze requires --catalog and --queries')
    print(json.dumps(freeze(directory,args.catalog,args.queries) if args.action=='freeze' else score(directory), indent=2))


if __name__=='__main__':
    main()
