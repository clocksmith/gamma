"""Exercise the approved answer path across the whole eligible inventory.

Independent evidence is reused only for byte-identical code from the completed
source qualification. Public examples actually execute again through answer().
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

from .approved_library import load_context
from .answer import answer
from .library_audit import inputs, original_for, exact_query, sha, write
from .records import LANE_ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', required=True, type=Path)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if not args.name.replace('-','').isalnum():
        raise ValueError('Invalid run name')
    directory = LANE_ROOT/'runs'/args.name
    _, entries, problems, boundary = inputs()
    files = sorted((LANE_ROOT/'algsolve').rglob('*.py')) + [args.catalog,
        LANE_ROOT/'contracts/lookup_thresholds.json', LANE_ROOT/'contracts/statement_lookup_thresholds.json']
    contract = {'files_sha256':{str(p.absolute().relative_to(LANE_ROOT.absolute())):sha(p) for p in files},
                'entries':len(entries), 'protected_excluded':len(boundary['keys']),
                'source_evidence':'Catalog independent verdicts reused only for byte-identical returned code',
                'execution':'Actual qualified answer path and public execution for each eligible indexed statement'}
    directory.mkdir(parents=True, exist_ok=True)
    if (directory/'contract.json').exists() and json.loads((directory/'contract.json').read_text())!=contract:
        raise ValueError('Verification contract changed')
    write(directory/'contract.json',contract)
    started = time.perf_counter()
    context, catalog = load_context(args.catalog)
    write(directory/'opening.json', {'context_seconds':time.perf_counter()-started,
          'encoder_loaded':context.embedder.encoder is not None,'os_caches_flushed':False,
          'scope':'context construction only; shared host, not an isolated latency comparison'})
    output = directory/'answers.jsonl'
    rows = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
    done = {r['key'] for r in rows}
    if len(rows)!=len(done) or not done <= {e.key for e in entries}:
        raise ValueError('Invalid prior verification')
    with output.open('a') as stream:
        for entry in entries:
            if entry.key in done:
                continue
            original, _ = original_for(entry,problems)
            result = answer(context, exact_query(entry,original), approved_library=catalog)
            approved = entry.key in catalog.manifest['approved']
            code_sha = hashlib.sha256(result['code'].encode()).hexdigest() if result.get('code') else None
            expected = catalog.manifest['approved'].get(entry.key, {})
            ok = ((result['decision']=='answered' and (result.get('match') or {}).get('key')==entry.key
                   and result['example_passed'] and code_sha==expected['code_sha256']) if approved
                  else result['decision']=='abstain' and result.get('code') is None)
            row = {'key':entry.key,'approved':approved,'passed':bool(ok),'code_sha256':code_sha,
                   'result':{k:v for k,v in result.items() if k!='code'}}
            rows.append(row); stream.write(json.dumps(row)+'\n'); stream.flush()
            if len(rows)%100==0:
                print(f'[qualified-path] {len(rows)}/{len(entries)}',flush=True)
    summary = {'entries':len(rows),'complete':len(rows)==len(entries),
               'approved_answered':sum(r['approved'] and r['passed'] for r in rows),
               'excluded_abstained':sum(not r['approved'] and r['passed'] for r in rows),
               'failures':[r for r in rows if not r['passed']],
               'encoder_loaded':context.embedder.encoder is not None,
               'catalog_sha256':sha(args.catalog),'contract_sha256':sha(directory/'contract.json')}
    write(directory/'summary.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
