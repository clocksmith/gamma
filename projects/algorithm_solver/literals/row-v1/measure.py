"""Freeze a bounded matched100 search with source/dictionary ablations."""
import argparse,hashlib,importlib.util,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PILOT=ROOT.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def module(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rw=module("row_rw",PILOT/"rewrite-v1/search.py")
scale=module("row_scale",PILOT/"scale100-v1/search.py")
joint=rw.joint
def main():
    p=argparse.ArgumentParser();p.add_argument("--run",type=Path,required=True);a=p.parse_args();run=a.run.resolve()
    ss,meta,admitted,banned=scale.load(run)
    prior={pid:{v:t for v,t in vs.items() if not v.startswith("row-")} for pid,vs in ss.items()}
    assert len(ss)==len(prior)==100 and all(prior.values())
    out=run/"search";out.mkdir()
    limits={"rounds_per_start":6,"trials_per_start":1600,"seconds_per_start":180,"addition_shortlist":24,"removal_shortlist":4,"pair_addition_shortlist":6,"pair_removal_sets":3}
    c={"schema":"gamma.literal-row-search-contract.v1","problems":100,"rows":[62,63,64,72,97],"limits":limits,
       "objective":["selections","package_bytes"],"candidate_rule":"AST fragments plus existing encoded spans; shared by at least two distinct problems; no full solve body or whole solution; ASCII96 retained",
       "pool_sha256":sha((run/"pool.json").read_bytes()),"qualification_sha256":sha((run/"qualification/report.json").read_bytes()),
       "code_hashes":{str(p):sha(p.read_bytes()) for p in [ROOT/"measure.py",ROOT/"pool.cjs",PILOT/"scale100-v1/search.py",PILOT/"rewrite-v1/search.py",PILOT/"rewrite-v1/fragment-proposals.cjs",PILOT/"joint-v1/search.py",PILOT/"scale-v2/search.py"]},
       "seeds":{str(w):{"file":str((run.parent/f"literal-heap-v1/full100-{2**w}/dictionary.json").resolve()),"sha256":sha((run.parent/f"literal-heap-v1/full100-{2**w}/dictionary.json").read_bytes())} for w in [7,8]}}
    joint.write(run/"search-contract.json",c)
    def proposals(s,state,limit):
        return list(dict.fromkeys(rw.ast_rank(s,state["vocab"],admitted,limit//2)+[x for x in rw.old_proposals(s,state,limit) if x not in banned][:limit//2]))
    joint.proposals=proposals;records=[];start=time.monotonic()
    for w in [7,8]:
        vocab=json.loads(Path(c["seeds"][str(w)]["file"]).read_text());assert not set(vocab)&banned
        baseline=joint.evaluate(prior,vocab,w);source=joint.evaluate(ss,vocab,w)
        initial,removed=joint.prune(ss,source,w)
        final,trace=joint.improve(ss,initial,w,"input",limits)
        joint.write(out/f"trace-{w}.json",{"initial_dictionary":initial["vocab"],"initial_sources":initial["chosen"],"initial":joint.brief(initial),"initial_pruned":removed,**trace})
        states=[("baseline",prior,baseline),("source-only",ss,source),("dictionary-only",prior,joint.evaluate(prior,final["vocab"],w)),("joint",ss,final)]
        for label,pool,state in states:
            name=f"{label}-{2**w}";metrics=rw.save(out/name,pool,meta,state,w,label)
            records.append({"label":name,"metrics":metrics,"manifest_sha256":sha((out/name/"manifest.json").read_bytes())})
        print(json.dumps({"arm":w,"baseline":joint.brief(baseline),"source_only":joint.brief(source),"joint":joint.brief(final)}),flush=True)
    joint.write(out/"summary.json",{"schema":"gamma.literal-row-search.v1","records":records,"elapsed_seconds":time.monotonic()-start,"contract_sha256":sha((run/"search-contract.json").read_bytes()),"scope":"100 consumed development problems;five source rewrites;no autonomous solving or new admission."})
if __name__=="__main__":main()
