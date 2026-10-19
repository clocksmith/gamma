"""Calibrate the complete public-check gate on consumed development queries.

Ranking alone overstates acceptance: an incompatible answer fails public checks.
This records that check once per top candidate, then fits score/margin thresholds
without testing alternatives. No hidden tests or fresh queries are read.
"""
import argparse
from dataclasses import replace
import json
import math
from pathlib import Path

from . import paraphrase, splits
from .answer import check_stored
from .library_audit import inputs, sha, write
from .lookup import decide
from .public_examples import recover
from .records import LANE_ROOT


def fit(rows):
    usable = [r for r in rows if r['candidates']]
    scores = {r['candidates'][0]['score'] for r in usable}
    scores.add(math.nextafter(max(scores), math.inf))
    margins = {0.0} | {r['candidates'][0]['score']-r['candidates'][1]['score']
                      for r in usable if len(r['candidates'])>1}
    best = None
    for score in sorted(scores):
        for margin in sorted(margins):
            th = {'min_score':score, 'min_margin':margin}
            accepted = [(decide(r['candidates'],th).key,r['target'])
                        for r in usable if r['public_passed']]
            wrong = sum(key is not None and key!=target for key,target in accepted)
            correct = sum(key is not None and key==target for key,target in accepted)
            quality = (-wrong, correct, -score, -margin)
            if best is None or quality>best[0]:
                best = quality, th, correct, wrong
    return dict(best[1],dev_correct=best[2],dev_wrong=best[3],dev_cases=len(rows),
                fitted_on='Consumed statement development, top candidate public gate; no fallback or independent tests')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--name',required=True)
    args = parser.parse_args()
    if not args.name.replace('-','').isalnum():
        raise ValueError('Invalid run name')
    _, entries, problems, _ = inputs()
    by_key = {e.key:e for e in entries}
    manifest = splits.load_manifest()
    queries = {q['qid']:q for q in manifest['recognition_dev']+manifest['recognition']}
    paragraphs = {r['key']:r for r in map(json.loads,paraphrase.PARAPHRASES_PATH.read_text().splitlines())}
    files = [args.source/'queries.jsonl',args.source/'contract.json']+sorted((LANE_ROOT/'algsolve').rglob('*.py'))
    contract = {'input_sha256':{str(p.resolve().relative_to(LANE_ROOT.resolve())):sha(p) for p in files},
                'source_contract':json.loads((args.source/'contract.json').read_text()),
                'scope':'Consumed development only. Public checks reject top candidates; never search for a passing sibling.'}
    out = LANE_ROOT/'runs'/args.name
    out.mkdir(parents=True,exist_ok=False)
    write(out/'contract.json',contract)
    rows = []
    with (out/'checks.jsonl').open('w') as stream:
        for ranked in map(json.loads,(args.source/'queries.jsonl').read_text().splitlines()):
            q = queries[ranked['qid']]
            source = problems.get(q.get('problem_uid'))
            if source is None and q.get('target') in by_key:
                source = next((problems[u] for u in by_key[q['target']].members if u in problems),None)
            verdict = None
            if source and ranked['reranked']:
                text = (source.statement if q['kind']=='absent_exact' else
                        by_key[q['target']].statement if q['kind']=='exact' else paragraphs[q['target']]['paraphrase'])
                query = replace(recover(source),statement=text,slug='',entry={},params=[],starter_code='',
                                hidden_tests_path='',reference_solutions=[],import_notes={})
                if query.public_tests:
                    _, verdict = check_stored(query,by_key[ranked['reranked'][0]['key']],30)
            row = {'qid':q['qid'],'target':q['target'],'candidates':ranked['reranked'],
                   'public_passed':bool(verdict and verdict.passed),
                   'public':verdict.to_dict() if verdict else None}
            rows.append(row); stream.write(json.dumps(row)+'\n'); stream.flush()
    thresholds = fit(rows)
    write(out/'thresholds.json',thresholds)
    print(json.dumps(thresholds))


if __name__=='__main__':
    main()
