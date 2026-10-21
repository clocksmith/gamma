"""Bind a five-problem semantic rewrite to frozen100 source and test identities."""
import argparse,hashlib,importlib.util,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PILOT=ROOT.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument("--prior-run",type=Path,required=True);p.add_argument("--proposal",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    source_pool=json.loads((a.prior_run/"pool.json").read_text());old=json.loads((a.prior_run/"contract.json").read_text())
    assert sha((a.prior_run/"contract.json").read_bytes())==json.loads((PILOT/"scale100-v1/evidence/audit.json").read_text())["contract_sha256"]
    methods=json.loads(a.proposal.read_text());assert sorted(map(int,methods))==[62,63,64,72,97]
    s=importlib.util.spec_from_file_location("row_cases",PILOT/"scale-v2/checks.py");checks=importlib.util.module_from_spec(s);s.loader.exec_module(checks)
    a.output.mkdir(exist_ok=False);(a.output/"inputs").mkdir();rows=[]
    for pid in [62,63,64,72,97]:
        baseline=next(r for r in source_pool["rows"] if r["id"]==pid and r["variant"]==("old-compact" if pid in [62,64] else "compact"))
        source=Path(baseline["file"]).read_bytes();assert sha(source)==baseline["sha256"]
        if pid in [62,64]:tests=checks.make_cases(pid)
        else:
            previous=next(r for r in old["rows"] if r["id"]==pid)
            raw=(a.prior_run/previous["test_file"]).read_bytes()
            assert sha(raw)==previous["test_sha256"]
            tests=json.loads(raw)
        prior_count=len(tests)
        if pid==62:
            for dims in [(20,20),(30,30),(100,100)]:tests.append({"args":list(dims),"expected":math.comb(sum(dims)-2,dims[0]-1)})
        source_file=f"inputs/{pid}.js";test_file=f"inputs/{pid}-tests.json"
        (a.output/source_file).write_bytes(source);(a.output/test_file).write_text(json.dumps(tests,indent=2)+"\n")
        rows.append({"id":pid,"baseline_file":baseline["file"],"source_file":source_file,"source_sha256":sha(source),"test_file":test_file,"test_sha256":sha((a.output/test_file).read_bytes()),"compare":"return","prior_cases":prior_count,"cases":len(tests),"additional_case_policy":"Independent binomial oracle for Number/BigInt boundary" if pid==62 else None})
    (a.output/"proposals.json").write_bytes(a.proposal.read_bytes())
    contract={"schema":"gamma.literal-row-contract.v1","parent_commit":"c652f7ad1a7577f628b4f6e5f111d5c145dc08ff",
      "scope":"Five consumed development problems use one explicitly counted rolling-row helper. Frozen100 denominator/dictionaries; no protected, recognition, admission or autonomous work.",
      "prior_pool_sha256":sha((a.prior_run/"pool.json").read_bytes()),"prior_run":str(a.prior_run.resolve()),"proposal_sha256":sha(a.proposal.read_bytes()),"helper_sha256":sha((ROOT/"row.js").read_bytes()),"rows":rows,
      "requirements":["No caller mutation or alias changes","Preserve BigInt behavior for62 and Number/Boolean results elsewhere","O(rows*columns) work,O(columns) storage; no maximum-bound runtime claim","Callbacks and helper code are complete source strings, counted in every encoded program; no decoder substitution"],
      "limits":{"qualification_seconds":180,"batch_cases":32,"max_sources":20,"max_artifact_bytes":67108864,"workers":1},
      "code_hashes":{str(p.resolve()):sha(p.read_bytes()) for p in [ROOT/"prepare.py",ROOT/"generate.cjs",ROOT/"verify.py",ROOT/"row.js",ROOT/"test-row.cjs",ROOT/"test-verifier.py",ROOT/"harness.cjs",PILOT/"rewrite-v1/generate.cjs",PILOT/"scale100-v1/qualify.py",PILOT/"scale-v2/checks.py",PILOT.parent/"algsolve/judge/sandbox.py",PILOT.parent/"algsolve/judge/judge.py"]}}
    (a.output/"contract.json").write_text(json.dumps(contract,indent=2)+"\n");print(json.dumps({"problems":5,"cases":sum(r["cases"] for r in rows),"contract_sha256":sha((a.output/"contract.json").read_bytes())}))
if __name__=="__main__":main()
