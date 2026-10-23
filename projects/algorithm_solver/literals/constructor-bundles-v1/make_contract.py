"""Bind exclusively from item32's public frozen metadata. Never read private paths."""
import os
if not __debug__ or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
    raise RuntimeError('Normal Python assertions required')
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build():
    parent_path=LIT/'stacking-structured-v1/contract.json'
    old=json.loads(parent_path.read_text());assert old['source_bound'] and old['source_arm']=='D11'
    c=copy.deepcopy(old)
    c.update(schema='gamma.constructor.bundles.v1',execution_status='bound_requires_root_and_claude_review_pushed_freeze_and_nonoverlap_queue',
             source_selection='D11_fixed_before_item39_private_probe',all_cores=[0,1,2,3],cores=[[0],[1],[2],[3]],
             limits={'address_space_bytes':8589934592,'overall_seconds':1800},search={'trials':10000,'seconds':300},
             arms={'L1':'literal_single','T1':'typed_single','LB':'literal_atomic','TB':'typed_atomic'},
             pool_caps={'prefix':32,'identifier':64,'literal':256,'operand':256},
             bundle_caps={'prefix':12,'identifier':12,'operand_packs':24,'literal_windows':32,'literal_bundles':56,
                          'maximum_additions':5,'deletion_shortlist':12,'deletion_combinations':12},
             source_binding={'method':'inherit_existing_public_item32_contract_only_no_private_reads',
                             'parent_contract_sha256':sha(parent_path),'parent_recorded_commit':'5d0ee7ccd'})
    c['code_hashes']['stacking-structured-v1/contract.json']=sha(parent_path)
    for p in sorted(HERE.iterdir()):
        if p.suffix in ('.py','.cjs','.md'):
            c['code_hashes'][str(p.relative_to(LIT))]=sha(p)
    # Copies are intentionally byte-identical codec/parser/decoder, with source hashes pinned.
    for name in ('codec.py','extract.cjs','decoder.cjs'):
        assert sha(HERE/name)==sha(LIT/'stacking-structured-v1'/name)
    c['decoder_dependencies']={'literal':[str(LIT/'literals.py'),str(LIT/'pass2/working/bitpack.py')],
                              'typed':[str(HERE/'decoder.cjs'),'/usr/share/nodejs/acorn/dist/acorn.js']}
    c['decoder_bytes']={kind:sum(Path(p).stat().st_size for p in paths) for kind,paths in c['decoder_dependencies'].items()}
    c['offline_encoder_files']={str(LIT/rel):digest for rel,digest in c['code_hashes'].items()
                              if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
    c['offline_encoder_files']['/usr/share/nodejs/acorn/dist/acorn.js']=sha('/usr/share/nodejs/acorn/dist/acorn.js')
    c['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in c['offline_encoder_files'])
    return c


if __name__=='__main__':
    target=HERE/'contract.json';target.write_text(json.dumps(build(),sort_keys=True,indent=2)+'\n');print(target)
