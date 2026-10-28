"""A narrowly scoped per-invocation ownership witness for the actual frozen judge adapter."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import protocol as p

FIELDS={'distinct_from_raw_packet','packet_unchanged_during_current_mutation',
        'distinct_from_prior_calls','current_unchanged_by_prior_mutation'}


def artifacts():
    paths=[HERE/'proof.py',HERE/'probe.py',HERE/'probe.js',HERE.parent/'harness.py',
           HERE.parent/'frozen-contract.json',p.ROOT/p.original.TRANSPORT/'harness.cjs',
           HERE.parent/'sources/python/442.py',HERE.parent/'sources/javascript/442.js']
    return {str(x.relative_to(p.ROOT)):p.sha(x.read_bytes()) for x in paths}


def packet():
    shared=[2,3]
    # Reuse one host object deliberately; JSON serialization and the real transport
    # must deliver exclusive child-side buffers, despite this host-side aliasing.
    return {'entry':'solve','calls':[{'args':[shared]} for _ in range(16)]}


def check(language,metadata,raw):
    if metadata['exit_code']!=0 or metadata['timed_out'] or metadata['output_limit_exceeded']:return False
    records=p.original.parse(raw,16)
    for record in records:
        result=record.get('result')
        if (record.get('result_type') != ('dict' if language=='python' else 'object')
                or type(result) is not dict or set(result)!=FIELDS or not all(v is True for v in result.values())
                or not p.o.exact(record.get('args_before'),[[2,3]])
                or not p.o.exact(record.get('args_after'),[[2,3]])
                or record.get('alias_edges')!=[]):return False
    return True


def freeze(args):
    repaired=json.loads((HERE.parent/'frozen-contract.json').read_bytes())
    assert p.original.runtime()==repaired['runtime']
    p.write(args.freeze,{'schema':'gamma.batch04-json-owned-buffer-probe.v1','artifact_hashes':artifacts(),
            'runtime':repaired['runtime'],'limits':asdict(p.LIMITS),'argv':p.ARGV,
            'packet_sha256':p.sha(p.encoded(packet())),
            'repair_freeze_sha256':p.sha((HERE.parent/'frozen-contract.json').read_bytes()),
            'scope':'Actual frozen isolated observer on primitive integer arrays only; no production/native/shared-input admission',
            'production_adapter_verified':False,'immutable_input_qualified':False})
    print('FROZEN',p.sha(args.freeze.read_bytes()),flush=True)


def run(args):
    raw=args.freeze.read_bytes();assert p.sha(raw)==args.freeze_sha256;contract=json.loads(raw)
    assert artifacts()==contract['artifact_hashes'] and p.original.runtime()==contract['runtime']
    assert asdict(p.LIMITS)==contract['limits'] and p.ARGV==contract['argv']
    args.output.mkdir(parents=True,exist_ok=False)
    p.write(args.output/'run-identity.json',{'freeze_sha256':p.sha(raw),'artifact_hashes':artifacts(),'host':platform.node()})
    results=[]
    for language,ext,harness in [('python','py','harness.py'),('javascript','js','harness.cjs')]:
        helper=(HERE.parent/'harness.py') if language=='python' else p.ROOT/p.original.TRANSPORT/'harness.cjs'
        result=p.original.sandbox.run(p.ARGV[language],files={'program.'+ext:(HERE/('probe.'+ext)).read_bytes(),harness:helper.read_bytes(),'inputs.json':p.encoded(packet())},limits=p.LIMITS)
        metadata=asdict(result)
        for stream in ('stdout','stderr'):
            payload=metadata.pop(stream);(args.output/(language+'.'+stream)).write_bytes(payload);metadata[stream+'_sha256']=p.sha(payload)
        p.write(args.output/(language+'.result.json'),metadata)
        results.append({'language':language,'calls':16,'passed':check(language,metadata,result.stdout)})
    p.write(args.output/'report.json',{'freeze_sha256':p.sha(raw),'results':results,'all_passed':all(r['passed'] for r in results),
            'production_adapter_verified':False,'immutable_input_qualified':False,'canonical_admission_changed':False})


def replay(args):
    raw=args.freeze.read_bytes();contract=json.loads(raw);assert artifacts()==contract['artifact_hashes']
    identity=json.loads((args.output/'run-identity.json').read_bytes());assert identity['freeze_sha256']==p.sha(raw) and identity['artifact_hashes']==contract['artifact_hashes']
    assert p.sha(p.encoded(packet()))==contract['packet_sha256'];results=[]
    for language in ('python','javascript'):
        metadata=json.loads((args.output/(language+'.result.json')).read_bytes())
        for stream in ('stdout','stderr'):assert p.sha((args.output/(language+'.'+stream)).read_bytes())==metadata[stream+'_sha256']
        results.append({'language':language,'calls':16,'passed':check(language,metadata,(args.output/(language+'.stdout')).read_bytes())})
    report={'freeze_sha256':p.sha(raw),'results':results,'all_passed':all(r['passed'] for r in results),
            'production_adapter_verified':False,'immutable_input_qualified':False,'canonical_admission_changed':False}
    assert json.loads((args.output/'report.json').read_bytes())==report
    return {'schema':'gamma.batch04-owned-buffer-raw-replay.v1','freeze_sha256':p.sha(raw),'calls_replayed':32,
            'all_passed':report['all_passed'],'raw_artifact_hashes':{x.name:p.sha(x.read_bytes()) for x in sorted(args.output.iterdir()) if x.is_file() and x.name!='replay.json'},
            'production_adapter_verified':False,'immutable_input_qualified':False,'canonical_admission_changed':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=('freeze','run','replay'));parser.add_argument('--freeze',type=Path,required=True);parser.add_argument('--output',type=Path);parser.add_argument('--freeze-sha256');args=parser.parse_args()
    if args.operation=='freeze':freeze(args)
    elif args.operation=='run':run(args)
    else:
        result=replay(args);p.write(args.output/'replay.json',result);print(json.dumps({k:v for k,v in result.items() if k!='raw_artifact_hashes'}))
