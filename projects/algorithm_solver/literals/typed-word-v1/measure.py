"""Replay authored semantic graphs only; no corpus, source service or case store."""
import hashlib
import json
from pathlib import Path
import sys

PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PROJECT))
from algsolve.synth import typed_word_codec as codec


def ref(name): return {'ref':name}
def lit(value): return {'literal':value}
def pure(name,*args): return {'op':name,'args':list(args)}
def bind(name,value,op='let'): return {'op':op,'name':name,'value':value}
def call(name,out,*args): return {'op':'call','operator':name,'out':out,'args':list(args)}
def graph(profile,inputs,body,answer,output):
    return {'schema':codec.runtime(profile).SCHEMA,'parameters':list(inputs),'inputs':inputs,
        'body':body,'return':answer,'output_type':output}


def fixtures():
    yield 'signed_constant','base-v2',graph('base-v2',{},[],lit(-257),'int'),{},-257
    yield 'mutable_sum','base-v2',graph('base-v2',{'values':['list','int']},[
        bind('sum',lit(0),'var'),{'op':'for','item':'item','in':ref('values'),
        'body':[bind('sum',pure('add',ref('sum'),ref('item')),'set')]}],ref('sum'),'int'),{'values':[4,-2,9]},11
    yield 'map_zero_default','base-v2',graph('base-v2',{},[
        call('map.new','map'),call('map.set','set',ref('map'),lit(3),lit(0)),
        call('map.get','found',ref('map'),lit(3),lit(99))],ref('found'),'int'),{},0
    yield 'vector_snapshot','vector-v1',graph('vector-v1',{},[
        call('vector.new','builder'),call('vector.append','first',ref('builder'),lit(4)),
        call('vector.snapshot','old',ref('builder')),call('vector.append','second',ref('builder'),lit(9)),
        call('vector.snapshot','new',ref('builder'))],pure('tuple',ref('old'),ref('new')),
        ['tuple',['list','int'],['list','int']]),{},([4],[4,9])


def measure():
    rows=[]
    for label,profile,program,arguments,expected in fixtures():
        ir=codec.runtime(profile); canonical=codec.canonicalize(program,profile)
        assert ir.execute(program,arguments)==expected
        values=[arguments[p] for p in program['parameters']]
        for width in (6,7,8):
            packet,cost=codec.encode(program,width,profile)
            decoded=codec.decode(packet)
            assert decoded==canonical
            assert ir.execute(decoded,dict(zip(decoded['parameters'],values)))==expected
            assert codec.execute(packet,values)==expected
            rows.append({'fixture':label,'packet_sha256':hashlib.sha256(packet).hexdigest(),
                'canonical_graph_sha256':hashlib.sha256(ir.canonical(canonical).encode()).hexdigest(),
                'roundtrip_exact':True,'packet_execution_passed':True,'authored_expected_result_passed':True,**cost})
    descriptors={p:codec.descriptor(p) for p in codec.PROFILES}
    packages=[]
    for width in (6,7,8):
        for profile,d in descriptors.items():
            selected=[r for r in rows if r['width']==width and r['profile']==profile]
            packet_bits=sum(r['packet_bits'] for r in selected)
            support_bits=8*(d['dictionary_bytes']+d['decoder_source_bytes']+d['runtime_source_bytes'])
            packages.append({'width':width,'profiles':[profile],'authored_graphs':len(selected),
                'packet_bits':packet_bits,'shared_support_bits':support_bits,
                'package_bits':packet_bits+support_bits,'support_charged_once':True})
        selected=[r for r in rows if r['width']==width]
        packet_bits=sum(r['packet_bits'] for r in selected)
        # One decoder implementation; both profile dictionaries and runtimes.
        support_bits=8*(descriptors['base-v2']['decoder_source_bytes']+
            sum(d['dictionary_bytes']+d['runtime_source_bytes'] for d in descriptors.values()))
        packages.append({'width':width,'profiles':list(codec.PROFILES),'authored_graphs':len(selected),
            'packet_bits':packet_bits,'shared_support_bits':support_bits,
            'package_bits':packet_bits+support_bits,'support_charged_once':True})
    return {'schema':'algsolve.typed-word-authored-measurement.v1',
        'evidence_scope':'four authored graph fixtures at three widths; not catalogue coverage or native qualification',
        'fixture_count':4,'rows':rows,'profiles':descriptors,'amortized_packages':packages,
        'width_comparison':'same semantic vocabulary; 7/8-bit words only increase payload cost in this version',
        'measurement_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__=='__main__':
    print(json.dumps(measure(),indent=2,sort_keys=True))
