#!/usr/bin/env python3
"""Source-bound observation/parity and P/K/F/S gates using existing cached codecs.

The frozen population may be synthetic or corpus data. This driver never builds,
selects a population, installs a dependency, or grants qualification by itself.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import midas_open_corpus_gate_v1 as base
from tools import midas_open_codec_v1 as parent
from tools import midas_open_boundary_observer_v1 as observer
from lib.fx2_native_gate_v1 import NativeGate

SELF = "tools/midas_open_observed_gate_v1.py"
UNIT = "operations/evidence/20260906_midas_open_boundary_observer_unit.json"
PLAN_SCHEMA = "gamma.enwiki9.midas-open-observed-gate-plan.v1"
require, read, digest = base.require, base.bounded_read, base.digest


def validate_plan(plan, candidate):
    require(set(plan) == {"schema", "candidate_id", "population", "builds", "resources",
                          "phase_wall_seconds", "runtime_files", "population_kind"}, "plan fields differ")
    require(plan["schema"] == PLAN_SCHEMA and plan["candidate_id"] == candidate, "plan identity differs")
    require(plan["population_kind"] in ("synthetic", "corpus"), "population kind is unbound")
    require(set(plan["builds"]) == {"parent", "observer"}, "both implementations are required")
    # Reuse the established resource and population policy unchanged.
    base.validate_plan({k:plan[k] for k in ("candidate_id", "population", "resources", "phase_wall_seconds")} |
                       {"schema":base.PLAN_SCHEMA,"cached_manifest":{},"cached_binary":{}}, candidate)
    require(isinstance(plan["runtime_files"],list) and plan["runtime_files"], "runtime inventory missing")
    require(len({r["path"] for r in plan["runtime_files"]}) == len(plan["runtime_files"]), "duplicate runtime file")


def authenticate(candidate, validate=False):
    require(__import__('re').fullmatch(r"[a-z0-9_]+",candidate) is not None, "invalid candidate")
    path = "operations/adaptive/experiments/" + candidate + ".json"
    data = read(ROOT/path,8*1024**2)
    reference = {"path":path,"sha256":"sha256:"+digest(data)}
    if not validate:
        require(json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]) == reference, "unbound invocation")
    contract = json.loads(data)
    require(contract["experimentId"] == candidate and contract["status"] == "frozen" and
            contract["registrationTiming"] == "prospective" and contract["objectiveCreditBytes"] == 0, "contract identity differs")
    inputs = base.contract_inputs(contract)
    for row in inputs.values(): base.reference_bytes(ROOT,row)
    plans = [r for r in inputs.values() if r["id"] == "observed-gate-plan"]
    require(len(plans) == 1 and SELF in inputs and UNIT in inputs, "runner, plan or unit authority missing")
    plan = json.loads(base.reference_bytes(ROOT,plans[0]));validate_plan(plan,candidate)
    require(contract["population"]["scopeBytes"] == plan["population"]["bytes"] and
            contract["population"]["scopeSymbols"] == 8*plan["population"]["bytes"], "population coordinates differ")
    require(plan["population"]["path"] in inputs, "unbound population")
    base.reference_bytes(ROOT,plan["population"])
    unit = json.loads(base.reference_bytes(ROOT,inputs[UNIT]))
    require(unit["validation"]["returncode"] == 0 and unit["validation"]["tests_passed"] == 5 and
            unit["corpus_executed"] is False, "observer unit did not pass")
    for row in unit["source_bindings"]:
        require(row["path"] in inputs and inputs[row["path"]]["sha256"].removeprefix('sha256:') == row["sha256"], "observer unit source unbound")
    manifests = {}
    for name, refs in plan["builds"].items():
        require(set(refs) == {"manifest","binary"}, "build reference fields differ")
        for row in refs.values():
            require(row["path"] in inputs, "build file is not an input")
            base.reference_bytes(ROOT,row)
        manifest = json.loads(base.reference_bytes(ROOT,refs["manifest"]))
        interface = parent if name == "parent" else types.SimpleNamespace(
            SOURCES=observer.SOURCES, FLAGS=parent.FLAGS, file_record=parent.file_record)
        base.verify_build_sources(interface,manifest,inputs)
        binary = base.reference_bytes(ROOT,refs["binary"])
        require(manifest["binary"] == {"bytes":len(binary),"sha256":digest(binary)}, "binary does not match manifest")
        if name == "observer":
            require(manifest["binary"] == {k:unit["binary"][k] for k in ("bytes","sha256")}, "observer binary lacks unit authority")
        manifests[name] = manifest
    for row in plan["runtime_files"]:
        require(Path(row["path"]).is_absolute() and parent.file_record(Path(row["path"])) == row, "runtime changed")
    return contract, plan, manifests


def equal(gate, label, left, right):
    if left != right:
        first = next((i for i,(a,b) in enumerate(zip(left,right)) if a != b),min(len(left),len(right)))
        gate.write(label+".json",{"equal":False,"first_byte":first,"left_bytes":len(left),"right_bytes":len(right),
                                 "left_hex":left[max(0,first-16):first+17].hex(),"right_hex":right[max(0,first-16):first+17].hex()})
        raise base.EvidenceFailure(label+" differs")


def compare_matrix(gate, binaries, population, phase_stop):
    raw = read(population,base.MAX_RAW);require(0 < len(raw) <= base.MAX_RAW,"raw bound differs")
    outcomes, archives = {}, {}
    for name,path in binaries.items(): gate.binaries[str(path)] = digest(read(path))
    for arm in "PKFS":
        directory = gate.result/arm;directory.mkdir()
        reference = directory/'reference'
        phase = arm+'-reference'
        gate.run(phase,[str(binaries['parent']),'encode',arm,str(len(raw)),str(population),str(reference)],phase_stop)
        base.operation_evidence(gate,parent,arm,'reference',reference,len(raw),len(raw))
        paths = {}
        for phase in ('encode','decode','repeat'):
            source = population if phase == 'encode' else directory/('encode' if phase == 'decode' else 'decode')/'data'
            output = directory/phase;operation = 'decode' if phase == 'decode' else 'encode'
            gate.run(arm+'-'+phase,[str(binaries['observer']),operation,arm,str(len(raw)),str(source),str(output),'digest'],phase_stop)
            require({p.name for p in output.iterdir()} == set(observer.FILES),'observer output set differs')
            observed = observer.validate_bundle(output)
            require(observed['summary'] == json.loads(read(gate.result/(arm+'-'+phase+'.stdout'))), 'observer stdout differs')
            require(observed['summary']['arm'] == arm and observed['summary']['operation'] == operation and
                    observed['summary']['raw_bytes'] == len(raw) and observed['summary']['max_raw_bytes'] == len(raw), 'observer coordinates differ')
            gate.required.update(output/name for name in observer.FILES);paths[phase] = output
        encoded = read(paths['encode']/'data');archives[arm] = encoded
        equal(gate,arm+'-inverse',read(paths['decode']/'data'),raw)
        equal(gate,arm+'-archive-repeat',read(paths['repeat']/'data'),encoded)
        equal(gate,arm+'-reference-archive',read(reference/'data'),encoded)
        equal(gate,arm+'-reference-state',read(reference/'state.bin'),read(paths['encode']/'state.bin'))
        gate.write(arm+'-reference-comparison.json',{'equal':True,'archive_and_complete_terminal_state_equal':True})
        for phase in ('decode','repeat'):
            result = observer.compare(paths['encode'],paths[phase],diagnostic=gate.result/(arm+'-'+phase+'-comparison.json'))
            require(result['equal'],arm+' boundary/probability divergence')
        costs = {c['phase'].split('-',1)[1]:{k:c.get(k) for k in ('elapsed_seconds','user_cpu_seconds','system_cpu_seconds')}
                 for c in gate.commands if c['phase'].startswith(arm+'-')}
        outcomes[arm] = {'archive_bytes':len(encoded),'archive_sha256':digest(encoded),'exact_inverse':True,
                         'exact_repeat':True,'unchanged_parent_archive_and_state':True,'all_boundaries_equal':True,'costs':costs}
    equal(gate,'PK-archive',archives['P'],archives['K'])
    pk = observer.compare(gate.result/'P/encode',gate.result/'K/encode',projection='parent')
    require(pk['equal'],'P/K parent projection differs')
    # The observer's parent comparison already covers authoritative parent/coder
    # state; also check the separately serialized reference-model projection.
    rows = [observer.boundary_rows(gate.result/arm/'encode/boundaries.jsonl',len(raw)) for arm in 'PK']
    for a,b in zip(*rows,strict=True):
        values = [next((x['bytes'],x['sha256']) for x in r['parts'] if x['name']=='reference_model_projection') for r in (a,b)]
        require(values[0] == values[1],'P/K reference projection differs at '+str(a['bit_position']))
    gate.write('PK-comparison.json',{**pk,'reference_model_projection_equal':True,'archive_equal':True})
    return {'infrastructure_pass':True,'arms':outcomes,'raw_bytes':len(raw),'native_phases':16,'all_boundaries_equal':True,
            'all_reference_archives_equal':True,'all_reference_final_states_equal':True,'pk_identity':True,
            'F_vs_P_archive_saved_bytes':len(archives['P'])-len(archives['F']),
            'F_vs_S_archive_saved_bytes':len(archives['S'])-len(archives['F'])}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--candidate',required=True)
    parser.add_argument('--validate-only',action='store_true');args=parser.parse_args()
    contract,plan,manifests=authenticate(args.candidate,args.validate_only)
    gate=NativeGate(ROOT,args.candidate,plan['resources'],args.validate_only)
    if args.validate_only:
        print(json.dumps({'status':'preflight_pass','population_kind':plan['population_kind'],'raw_bytes':plan['population']['bytes'],'native_phases':16,'executed':False}));return 0
    gate.required=set()
    stage={'schema':'gamma.enwiki9.midas-open-observed-stage.v1','candidate_id':args.candidate,'objective':contract['objective'],
           'experiment':gate.reference,'status':'running','infrastructure_pass':False,'population_kind':plan['population_kind'],
           'objective_credit_bytes':0,'complete_package_bytes':None,'full_corpus_score_bytes':None,'resource_qualified':False,
           'timing_authority':'shared-host diagnostic','continuous_guard_decision':'pending canonical outer closure',
           'larger_gate_authorized':False,'package_components':{n:m['binary']['bytes'] for n,m in manifests.items()},
           'synchronization_scope':'Every pre-truth Q16 and every32-byte complete serialized SHA256 state witness; no full snapshot reconstruction on this population.'}
    try:
        binaries={}
        for name,refs in plan['builds'].items():
            directory=gate.work/name
            for key,filename in [('binary','program'),('manifest','manifest.json')]:
                target=directory/filename;gate.copy(refs[key]['path'],target);target.chmod(0o500 if key=='binary' else 0o400)
                gate.retained[target]=refs[key]['sha256'].removeprefix('sha256:');gate.required.add(target)
            binaries[name]=directory/'program'
        population=gate.work/'population.raw';gate.copy(plan['population']['path'],population);population.chmod(0o400)
        gate.retained[population]=plan['population']['sha256'].removeprefix('sha256:');gate.required.add(population)
        stage.update(compare_matrix(gate,binaries,population,plan['phase_wall_seconds']),status='passed')
        require(len(gate.commands)==16,'phase population differs')
    except Exception as error:
        stage.update(status='failed',infrastructure_pass=False,failure_class=base.classify(error,gate.commands),error=type(error).__name__+': '+str(error))
    for c in gate.commands:
        gate.required.update(gate.result/(c['phase']+suffix) for suffix in ('.stdout','.stderr','.execution.json'))
    base.finalize(gate,stage,lambda:authenticate(args.candidate))
    print(json.dumps({k:stage[k] for k in ('status','infrastructure_pass','candidate_id')}))
    return 0 if stage['infrastructure_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
