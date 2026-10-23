"""Create an unbound draft by default; explicit later binding reads receipts only.

Binding is preparation, not launch authority. No source code is parsed here.
"""
import os
if not __debug__ or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
    raise RuntimeError('Assertion validation requires normal Python mode; PYTHONOPTIMIZE/-O is forbidden')

import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())


def build(source_run=None):
    prior = read(LIT/'identifier-templates-v1/contract.json')
    c = dict(schema='gamma.stacking.structured.v1',source_bound=False,
             execution_status='draft_requires_source_binding_and_cross_review_and_pushed_freeze',
             source_arm='D11',source_selection='fixed_before_results_not_validation_winner',
             python_bin='/home/x/deco/gamma/.venv_rocm/bin/python',python_version=platform.python_version(),
             partition=prior['partition'],search={'seconds':300,'trials':10000},
             all_cores=list(range(8)),cores=[[0,1],[2,3],[4,5],[6,7]],
             limits={'address_space_bytes':8589934592,'overall_seconds':1800},
             code_hashes={},runtime_files={},private_files={},source_qualification={},
             parent_evidence=None,
             source_run=None,model_bytes=0,training_steps=0,fresh_case_executions=0)
    dependencies = ['cost-decomposition-v1/analyze.py','literals.py','pass2/working/bitpack.py',
                    'expression-prefix-v1/extract.cjs','identifier-templates-v1/extract.cjs']
    own = ['codec.py','extract.cjs','decoder.cjs','search.py','run.py','launch.py','report.py',
           'make_contract.py','test_codec.py','test_search.py','test_report.py','FREEZE.md']
    for rel in dependencies+['stacking-structured-v1/'+p for p in own]:
        c['code_hashes'][rel] = sha(LIT/rel)
    for path in (c['python_bin'],shutil.which('node'),'/usr/share/nodejs/acorn/dist/acorn.js',
                 '/usr/share/nodejs/acorn/package.json'):
        c['runtime_files'][str(Path(path).resolve())] = sha(path)
    c['decoder_dependencies'] = {
        'literal':[str(LIT/'literals.py'),str(LIT/'pass2/working/bitpack.py')],
        'typed':[str(HERE/'decoder.cjs'),'/usr/share/nodejs/acorn/dist/acorn.js']}
    c['decoder_bytes'] = {kind:sum(Path(p).stat().st_size for p in paths)
                          for kind,paths in c['decoder_dependencies'].items()}
    c['offline_encoder_files'] = {str(LIT/rel):digest for rel,digest in c['code_hashes'].items()
        if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
    c['offline_encoder_files']['/usr/share/nodejs/acorn/dist/acorn.js'] = sha('/usr/share/nodejs/acorn/dist/acorn.js')
    c['offline_encoder_bytes'] = sum(Path(p).stat().st_size for p in c['offline_encoder_files'])
    c['runtime_inventory_scope'] = 'Source/parser bytes separately charged; Python/Node binaries pinned, complete interpreter installations not measured.'
    if source_run is not None:
        source_run = source_run.resolve()
        result = read(source_run/'results.json')
        parent_contract = LIT/'stacking-v1/contract.json'
        public_path = LIT/'stacking-v1/evidence/results.json'
        public = read(public_path)
        assert result['contract_sha256']==sha(parent_contract)==public['contract_sha256']
        assert public['private_results_sha256']==sha(source_run/'results.json')
        assert public['predictions']['S1_references_and_all_packets_replay'] is True
        c['parent_evidence']={'relative_path':'stacking-v1/evidence/results.json',
                              'sha256':sha(public_path),'private_results_sha256':public['private_results_sha256'],
                              'contract_sha256':sha(parent_contract),
                              'required_provenance':'published_by_item30_independent_packet_and_qualification_replay'}
        for path in (parent_contract,public_path):
            c['code_hashes'][str(path.relative_to(LIT))]=sha(path)
        receipt = read(source_run/'supervisor-receipt.json')
        assert receipt['complete'] and receipt['promotion_allowed'] and not receipt['outer_timeout']
        arm = next(a for a in result['arms'] if a['arm']=='D11' and a['policy']=='canonical')
        public_arm = next(a for a in public['arms'] if a['arm']=='D11' and a['policy']=='canonical')
        expected = {str(i) for group in c['partition'].values() for i in group}
        assert set(arm['per_problem']) == set(arm['qualification']) == expected
        assert arm['entries'] <= 256 and not arm['illegal_entry_sha256']
        for pid,row in arm['per_problem'].items():
            assert public_arm['per_problem'][pid]['source_sha256']==row['source_sha256']
            assert public_arm['qualification'][pid]==arm['qualification'][pid]
            assert row['encodable'] and row['qualified_source'] and arm['qualification'][pid]['passed']
            c['source_qualification'][pid] = {'passed':True,'source_sha256':row['source_sha256'],
                                              'receipt':arm['qualification'][pid]}
        for rel in ('results.json','supervisor-receipt.json','fit/D11/fit-sources.json',
                    'fit/D11/dictionary.json','artifacts/D11/dictionary.json','artifacts/D11/sources.json'):
            c['private_files'][rel] = sha(source_run/rel)
        assert c['private_files']['fit/D11/dictionary.json']==c['private_files']['artifacts/D11/dictionary.json']
        c.update(source_bound=True,source_run=str(source_run),
                 execution_status='bound_requires_cross_review_and_pushed_freeze')
    return c


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source-run',type=Path)
    a = p.parse_args()
    target = HERE/('contract.json' if a.source_run else 'contract.pending.json')
    target.write_text(json.dumps(build(a.source_run),sort_keys=True,indent=2)+'\n')
    print(target)
