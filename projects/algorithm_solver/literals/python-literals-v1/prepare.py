"""Freeze Python-only independently qualified sources; no optimization here."""
import argparse,importlib.util,json
from pathlib import Path
from search import joint,family
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
s=importlib.util.spec_from_file_location('python_adapted_pool_verifier',HERE/'verify.py');verification=importlib.util.module_from_spec(s);s.loader.exec_module(verification)

def pins():
    files=[HERE/n for n in ('prepare.py','run.py','search.py','CONTRACT.md','qualify.py','verify.py','harness.py','SEARCH_FREEZE.md')]
    files += [LIT/n/'search.py' for n in ('incremental-merge-v1','incremental-merge-v2','incremental-merge-v3','incremental-merge-v4','joint-composable-v1','compact-search-v1')]
    files += [LIT/'incremental-merge-v4/accelerator.py',LIT/'incremental-merge-v4/score_kernel.c',LIT/'readable-joint-blocks-v1/compare.py',LIT/'readable-joint-blocks-v1/transfer.py',joint.compare.CODEC_FILE,joint.compare.SCORER_FILE]
    result={str(p.relative_to(LIT.parent)):joint.b.sha(p.read_bytes()) for p in files}
    result.update(verification.q.pins());return result

def freeze(inputs,reports,output,kernel):
    if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private source/dictionary freeze outside repo required')
    spec,_=joint.b.module('python_literal_partition',LIT/'readable-joint-blocks-v1/transfer.py').load_manifest()
    fit=spec['partition']['dev_fit'];sources={};owners={};references={};families={};proofs=[];seen={}
    for report in reports:
        proof=verification.verify(inputs,report);proofs.append(proof)
        rc=json.loads((report.parent/'contract.json').read_text());sf=Path(rc['source_freeze']);sc,raw=verification.q.load_freeze(sf)
        for pid in proof['eligible_ids']:
            if pid not in fit:raise ValueError('non-fit source attempted to enter fitting')
            source=raw[pid];identity=(pid,joint.b.sha(source))
            if identity in seen:continue
            key=f'{pid}:python:{identity[1][:16]}'
            if key in sources:raise ValueError('truncated source-key collision')
            seen[identity]=key;text=source.decode();joint.compare.validate_texts({key:text})
            sources[key]={'path':str(sf/f'{pid}.py'),'sha256':identity[1],'bytes':len(source),'report_sha256':proof['report_sha256']};owners[key]=str(pid)
            if str(pid) not in references:references[str(pid)]=key;families[str(pid)]=family(text)
    if not sources:raise ValueError('no independently qualified adapted Python sources')
    contract={'schema':'gamma.python.systematic-literals.v1','language':'python','capacities':[128,256],'alphabet':'95printableASCII+LF','source_rows':sources,'owners':owners,'references':references,'families':families,'proofs':proofs,'code_sha256':pins(),'fixed_fit_ids':fit,'covered_fit_ids':sorted(map(int,references)),'uncovered_fit_ids':sorted(set(fit)-set(map(int,references))),'fixed_fit_population':300,'fit_population':len(references),'m1_population':500,'permitted_population':400,'validation_texts_loaded':False,'protected_access':False,'m1_qualified':False,'candidate_executions':0,'kernel_path':str(kernel),'kernel_binary_sha256':joint.b.sha(kernel.read_bytes()),'policy':'family32 local growth; overlap merging; exact redundancy removal; coupled adjacent composition/parent retirement with exact first-two-gate bound; no reset between phases','cpu_seconds_per_slice':240,'outer_wall_seconds':330,'memory_bytes':2*1024**3,'budget_policy':'bounded resumable CPU slices; no candidate execution; resource bounds are not metric tuning'}
    output.mkdir(parents=True,exist_ok=False);joint.b.write(output/'contract.json',contract);return contract

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--report',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--kernel',type=Path,required=True);a=p.parse_args();c=freeze(a.inputs,a.report,a.output,a.kernel);print(json.dumps({'status':'frozen','qualified_fit_problems':c['fit_population'],'fixed_fit_population':300,'variants':len(c['source_rows']),'m1_qualified':False}))
