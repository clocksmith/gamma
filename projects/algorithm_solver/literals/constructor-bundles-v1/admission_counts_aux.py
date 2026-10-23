"""Unpinned post-run metadata summary; does not change item39 execution or verdict.

Only reads an already independently audited report and completion receipts.
No sources, dictionaries, plans, search, qualification or recomputation of gates.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def summarize(report):
    assert report.get('verdict_available') is not False
    assert report['representation']=='separate_structured_2c'
    answer={}
    for arm in report['arms']:
        if arm['arm']=='D11':continue
        metadata=arm['atomic_admission'];moves=metadata['accepted_moves']
        counts=Counter(m['kind'] for m in moves)
        singles=[m for m in moves if m['addition_count']==1]
        bundles=[m for m in moves if m['addition_count']>=2]
        assert len(bundles)==metadata['accepted_atomic_moves']
        assert len(moves)==arm['fit_search']['search']['rounds']
        answer[arm['arm']]={'accepted_moves':len(moves),'accepted_singletons':len(singles),
            'accepted_bundles':len(bundles),'accepted_removal_only':sum(m['addition_count']==0 for m in moves),
            'accepted_literal_bundles':sum(m['kind']=='literal_bundle' for m in bundles),
            'accepted_constructor_bundles':sum(m['kind']=='constructor_bundle' for m in bundles),
            'singleton_via_constructor_bundle_stream':sum(m['kind']=='constructor_bundle' for m in singles),
            'accepted_by_stream':dict(sorted(counts.items())),
            'accepted_operand_installation_moves':metadata['accepted_operand_installations']}
        assert answer[arm['arm']]['accepted_literal_bundles']+answer[arm['arm']]['accepted_constructor_bundles']==len(bundles)
    assert set(answer)=={'L1','T1','LB','TB'}
    return {'schema':'gamma.constructor-bundles.admission-counts.aux.v1','frozen_execution_changed':False,
            'verdict_changed':False,'definitions':'Bundle means at least two absent keys added atomically; singleton means one. Proposal stream labels are also reported. Missing subsets are not inferred.',
            'arms':answer}


def main(folder):
    assert not (folder/'failure.json').exists()
    status=json.loads((folder/'status.json').read_text());receipt=json.loads((folder/'supervisor-receipt.json').read_text())
    assert status['complete'] and receipt['complete'] and receipt['promotion_allowed'] and not receipt['outer_timeout']
    raw=(folder/'report.json').read_bytes();result=summarize(json.loads(raw))
    result['audited_report_sha256']=hashlib.sha256(raw).hexdigest()
    (folder/'admission-counts-aux.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    lines=['# Item39 accepted admission counts (auxiliary)','',
           'Derived from the completed independently audited report; execution and verdict are unchanged.','',
           '| Arm | All accepted | Singletons | Bundles | Literal bundles | Constructor bundles | Removal only |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for arm,row in result['arms'].items():
        lines.append(f"| {arm} | {row['accepted_moves']} | {row['accepted_singletons']} | {row['accepted_bundles']} | {row['accepted_literal_bundles']} | {row['accepted_constructor_bundles']} | {row['accepted_removal_only']} |")
    (folder/'ADMISSION-COUNTS-AUX.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);main(parser.parse_args().run)
