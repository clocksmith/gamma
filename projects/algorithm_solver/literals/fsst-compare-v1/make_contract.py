import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((LIT/'binding-descent-v1/contract.json').read_text());work=Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1');up=Path('/home/x/deco-scratch/fsst-comparator')
c={'schema':'gamma.fsst-compare.v1','partition':old['partition'],'code_hashes':dict(old['code_hashes']),
   'gamma_decoder_bytes':old['decoder_dependency_bytes'],'native_decoder_bytes':sum((HERE/f).stat().st_size for f in ('native.py','packet.py')),
   'search':{'trials':5000,'seconds':300},'neighborhood':old['neighborhood'],
   'limits':{'workers':2,'address_space_bytes':4294967296,'overall_seconds':900},
   'upstream_commit':'e638d4cf8c26129d73c242a4127b42b975de5b63','upstream_repository':'https://github.com/cwida/fsst',
   'build_command':'c++ -std=c++17 -O3 -DNDEBUG -march=native -fPIC -shared -I UPSTREAM UPSTREAM/libfsst.cpp UPSTREAM/fsst_avx512.cpp wrapper.cpp -o libgamma_fsst.so',
   'compiler':'Ubuntu 15.2.0-16ubuntu1','library_path':str(work/'fsst-comparator-build/libgamma_fsst.so'),
   'pre_freeze_audit':{'corpus_measurements':False,'tests':8,'exhaustive_native_examples':100},'private_files':{},'cohorts':[]}
for name,arm in [('R','control'),('naming','scope_joint')]:
    rel=f'binding-descent/run-v1/{arm}-256';c['cohorts'].append({'name':name,'arm':arm,'relative_path':rel})
    for file in ('dictionary.json','fit-sources.json','sources.json','fit-seal.json'):c['private_files'][rel+'/'+file]=sha(work/rel/file)
for f in HERE.iterdir():
    if f.suffix in ('.py','.cpp') or f.name=='FREEZE.md':c['code_hashes'][str(f.relative_to(LIT))]=sha(f)
c['external_files']={str(up/f):sha(up/f) for f in ('fsst.h','libfsst.cpp','libfsst.hpp','fsst_avx512.cpp','fsst_avx512.inc','fsst_avx512_unroll1.inc','fsst_avx512_unroll2.inc','fsst_avx512_unroll3.inc','fsst_avx512_unroll4.inc','LICENSE','README.md')}
c['external_files'].update(old['runtime_files']);c['external_files'][c['library_path']]=sha(Path(c['library_path']))
c['native_library_bytes']=Path(c['library_path']).stat().st_size
c['historical_evidence_sha256']=sha(LIT/'binding-descent-v1/evidence/results.json');c['code_hashes']['binding-descent-v1/evidence/results.json']=c['historical_evidence_sha256']
c['code_hashes']['cost-decomposition-v1/evidence/results.json']=sha(LIT/'cost-decomposition-v1/evidence/results.json')
c['upstream_source_bytes']=sum((up/f).stat().st_size for f in ('fsst.h','libfsst.cpp','libfsst.hpp','fsst_avx512.cpp','fsst_avx512.inc','fsst_avx512_unroll1.inc','fsst_avx512_unroll2.inc','fsst_avx512_unroll3.inc','fsst_avx512_unroll4.inc'))
c['gamma_adapter_tooling_bytes']=sum((LIT/rel).stat().st_size for rel in c['code_hashes'] if rel.endswith(('.py','.cjs','.cpp')) and '/test_' not in rel)
(HERE/'contract.json').write_text(json.dumps(c,indent=2,sort_keys=True)+'\n')
