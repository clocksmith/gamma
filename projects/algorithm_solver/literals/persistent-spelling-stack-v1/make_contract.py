"""Public-only54 binding; exact46 science plus accepted52 execution authority."""
import argparse
import copy
from pathlib import Path
import common as c
import parser_adapter

# Explicit implementation inventory: later README/review/results must not alter
# the execution binding merely by being added to this directory.
FILES=('FREEZE.md','common.py','parser_adapter.py','engine.py','run.py',
       'qualification.py','supervise.py','make_contract.py','report.py',
       'ban_replay.py','current_best.py','test_parser_adapter.py','test_run.py',
       'test_supervise.py','test_contract.py','test_ban_replay.py',
       'test_current_best.py','test_report.py')


def merge_pins(target,addition):
    for key,value in addition.items():
        assert key not in target or target[key]==value,('Inherited authority drift',key)
        target[key]=value


def parent_authority():
    parent_path=c.LIT/'postfit-spelling-stack-v1/contract.json';parent=c.read(parent_path)
    c.verify_public(parent)
    failure_path=c.LIT/'postfit-spelling-stack-v1/evidence/incomplete.json';failure=c.read(failure_path)
    assert failure['complete'] is False and failure['scientific_verdict'] is None
    assert failure['contract_sha256']==c.hashfile(parent_path)
    assert failure['validation_started'] is False and failure['qualification_started'] is False
    pins_path=c.LIT/'persistent-spelling-parser-v1/timing-pins.json';pins=c.read(pins_path)
    evidence_path=c.LIT/'persistent-spelling-parser-v1/evidence/results.json';evidence=c.read(evidence_path)
    supervisor_path=c.LIT/'persistent-spelling-parser-v1/evidence/supervisor.json';supervisor=c.read(supervisor_path)
    assert evidence['complete'] is supervisor['complete'] is True
    assert evidence['synthetic_only'] is True and evidence['private_inputs'] is False
    assert supervisor['returncode']==0 and evidence['pin_sha256']==supervisor['pin_sha256']==c.hashfile(pins_path)
    assert evidence['fixture_sha256']==pins['fixture_sha256']
    assert len(evidence['blocks'])==4 and [row['block'] for row in evidence['blocks']]==pins['blocks']
    assert all(row['complete'] is True and row['semantics']==evidence['blocks'][0]['semantics'] for row in evidence['blocks'])
    assert pins['python_bin']==parent['python_bin'] and pins['python_version']==parent['python_version']
    for rel,digest in pins['code_hashes'].items():assert c.hashfile(c.LIT/rel)==digest,rel
    for path,digest in pins['runtime_files'].items():assert c.hashfile(path)==digest,path
    return parent,pins,[parent_path,failure_path,pins_path,evidence_path,supervisor_path]


def build():
    parent,pins,authorities=parent_authority();result=copy.deepcopy(parent)
    result.update(schema='gamma.persistent-spelling-stack.v1',active=False,
        prebinding_private_access=False,predecessor_run_reused=False)
    merge_pins(result['code_hashes'],pins['code_hashes']);merge_pins(result['runtime_files'],pins['runtime_files'])
    result['parser']={'implementation_sha256':parser_adapter.implementation(),'limits':dict(parser_adapter.LIMITS),
        'evidence':{'path':str(authorities[3].relative_to(c.LIT)),'sha256':c.hashfile(authorities[3])},
        'supervisor':{'path':str(authorities[4].relative_to(c.LIT)),'sha256':c.hashfile(authorities[4])},
        'pins':{'path':str(authorities[2].relative_to(c.LIT)),'sha256':c.hashfile(authorities[2])},
        'services_per_anchor':{'fit':1,'validation':1},'restart_on_failure':False,
        'execution_source_cache':False,'combined_memory_cap_claim':False,
        'memory_scope':'Each process inherits8GiB RLIMIT_AS; service observed VmHWM and worker peak RSS are separate, not a simultaneous aggregate.'}
    result['predecessor']={'contract':{'path':str(authorities[0].relative_to(c.LIT)),'sha256':c.hashfile(authorities[0])},
        'incomplete_record':{'path':str(authorities[1].relative_to(c.LIT)),'sha256':c.hashfile(authorities[1])},
        'failure_preserved':True,'scientific_retry_with_new_implementation':True}
    result['report_ban_replay']={'authority':'tail-search-v1/structure.cjs','batch_size':16,
        'phase_scoped':True,'persistent_parser_used':False,'execution_cache':False}
    for path in [*authorities,*(c.HERE/name for name in FILES)]:
        assert path.is_file(),('Missing reviewed implementation file',str(path))
        result['code_hashes'][str(path.relative_to(c.LIT))]=c.hashfile(path)
    result['runtime_files'][str(Path(result['python_bin']).resolve())]=c.hashfile(Path(result['python_bin']).resolve())
    result['offline_encoder_files']={str(c.LIT/rel):digest for rel,digest in result['code_hashes'].items()
        if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
    result['offline_encoder_bytes']=sum(Path(path).stat().st_size for path in result['offline_encoder_files'])
    result['runtime_inventory_scope']='Pinned46 and52 implementations/runtime union; installed runtime footprint unmeasured.'
    return result


def activate(current,pending):
    assert current==pending and pending['active'] is False and pending['source_bound'] is True,'Reviewed pending drift or unbound parents'
    result=copy.deepcopy(pending);result['active']=True;return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--activate',action='store_true');args=ap.parse_args()
    value=build();path=c.HERE/'pending-contract.json'
    if args.activate:value=activate(value,c.read(path));path=c.HERE/'contract.json'
    c.write(path,value);print(c.canonical({'path':str(path),'sha256':c.hashfile(path),'active':value['active'],'private_inputs_opened':False}))

if __name__=='__main__':main()
