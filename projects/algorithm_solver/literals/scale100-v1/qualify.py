"""Check only new source bytes, with existing independent tests and alias parity."""
import argparse, hashlib, importlib.util, json, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PILOT=HERE.parent
sys.path[:0]=[str(PILOT.parent),str(PILOT),str(PILOT/"pass2/working")]
from algsolve.judge import sandbox
from algsolve.judge.judge import FunctionalTest, _matches
from literals import dictionary_bytes
from bitpack import encode, decode
from verify_execution import strict_object
sha=lambda b:hashlib.sha256(b).hexdigest()
def exact(a,b):
    if isinstance(a,bool) or isinstance(b,bool):return type(a) is type(b) and a==b
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):return a==b
    if type(a) is not type(b):return False
    if isinstance(a,list):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if isinstance(a,dict):return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    return a==b
def effect_ok(pid,case,rec):
    before=case["args"];after=rec.get("args_after");edges=rec.get("alias_edges",[])
    if pid==56:
        return exact(after,[sorted(before[0],key=lambda r:r[0])]) and not edges
    if pid==66:
        return exact(after,[rec.get("result")]) and ["result","args.0"] in edges
    return exact(after,before)
def judge_record(pid,case,mode,rec,original=None):
    valid=exact(rec.get("args_before"),case["args"]) and _matches(FunctionalTest(args=case["args"],expected=case["expected"],compare=mode),rec) and effect_ok(pid,case,rec)
    observation={k:rec.get(k) for k in ["result","args_after","alias_edges","error"]}
    return valid and (original is None or exact(observation,original)),observation
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run",type=Path,required=True);a=ap.parse_args()
    run=a.run;contract_raw=(run/"contract.json").read_bytes();c=json.loads(contract_raw)
    manifest_raw=(run/"generated/manifest.json").read_bytes();m=json.loads(manifest_raw)
    assert m["contract_sha256"]==sha(contract_raw)
    for name,h in c["code_hashes"].items():assert sha((HERE/name).read_bytes())==h,name
    out=run/"qualification";out.mkdir();(out/"observations").mkdir()
    harness=(HERE/"harness.cjs").read_text();started=time.monotonic();rows=[];case_count=0
    for spec in c["rows"]:
        pid=spec["id"];test_raw=(run/spec["test_file"]).read_bytes();assert sha(test_raw)==spec["test_sha256"]
        tests=json.loads(test_raw);case_count+=len(tests);original=None
        variants=sorted((r for r in m["rows"] if r["id"]==pid),key=lambda r:(r["variant"]!="original",r["variant"]))
        for r in variants:
            if time.monotonic()-started>c["limits"]["qualification_seconds"]:raise TimeoutError("qualification budget")
            source=(run/"generated"/r["file"]).read_text();assert sha(source.encode())==r["sha256"]
            alphabet=sorted(set(source));assert len(alphabet)<=256
            source=decode(dictionary_bytes(alphabet),encode(alphabet,[alphabet.index(x) for x in source],8))
            passed=0;failures=[];calls=[];observations=[]
            for offset in range(0,len(tests),c["limits"]["batch_cases"]):
                batch=tests[offset:offset+c["limits"]["batch_cases"]]
                payload={"entry":r["entry"],"calls":[{"args":t["args"]} for t in batch]}
                result=sandbox.run(["/usr/bin/node","--jitless","--single-threaded","--max-old-space-size=64","harness.cjs"],files={"program.js":source,"inputs.json":json.dumps(payload),"harness.cjs":harness},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=c["limits"]["output_bytes"]))
                stem=f"{pid}-{r['variant']}-{offset}"
                for ext,data in [("stdout",result.stdout),("stderr",result.stderr)]:(out/"observations"/f"{stem}.{ext}").write_bytes(data)
                calls.append({"stem":stem,"exit_code":result.exit_code,"timed_out":result.timed_out,"wall_seconds":result.wall_seconds,"stdout_sha256":sha(result.stdout),"stderr_sha256":sha(result.stderr)})
                try:
                    assert result.ok,"sandbox failure"
                    records=[json.loads(line,object_pairs_hook=strict_object,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))) for line in result.stdout.splitlines()]
                    assert len(records)==len(batch)+1 and records[-1]=={"done":len(batch)}
                    for k,rec in enumerate(records[:-1]):
                        assert type(rec.get("i")) is int and rec["i"]==k
                        valid,obs=judge_record(pid,batch[k],spec["compare"],rec,None if r["variant"]=="original" else original[offset+k])
                        observations.append(obs);passed+=bool(valid)
                        if not valid:failures.append({"case":offset+k,"reason":"oracle_effect_or_original_parity"})
                except Exception as e:
                    failures.append({"offset":offset,"reason":"execution_or_protocol","detail":str(e)})
                    observations.extend([None]*max(0,offset+len(batch)-len(observations)))
            if r["variant"]=="original":original=observations
            rows.append({**r,"passed":passed==len(tests) and not failures,"checks_passed":passed,"checks_total":len(tests),"failures":failures,"calls":calls})
        print(json.dumps({"id":pid,"variants":len(variants),"passed":sum(r["passed"] for r in rows if r["id"]==pid)}),flush=True)
    report={"schema":"gamma.literal-scale100-qualification.v1","rows":rows,"source_count":len(rows),"passed_sources":sum(r["passed"] for r in rows),"checks_passed":sum(r["checks_passed"] for r in rows),"checks_total":sum(r["checks_total"] for r in rows),"distinct_cases":case_count,"elapsed_seconds":time.monotonic()-started,"contract_sha256":sha(contract_raw),"generated_manifest_sha256":sha(manifest_raw),"harness_sha256":sha(harness.encode()),"scope":"New20 development problems only. Earlier80 reuse prior native receipts. No corpus admission or autonomous result."}
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="rows"}))
if __name__=="__main__":main()
