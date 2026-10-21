"""Matched100-problem literal learning; all private encoded source stays local."""
import argparse, hashlib, importlib.util, json, time
from collections import defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent;PILOT=HERE.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location("scale100_rewrite",PILOT/"rewrite-v1/search.py");rw=importlib.util.module_from_spec(spec);spec.loader.exec_module(rw)
joint=rw.joint;base=rw.base
def load(run):
    p=json.loads((run/"pool.json").read_text());ss=defaultdict(dict);meta={};owners=defaultdict(set);banned=set()
    for r in p["rows"]:
        text=Path(r["file"]).read_text();assert sha(text.encode())==r["sha256"]
        ss[r["id"]][r["variant"]]=text;meta[r["id"],r["variant"]]=r;banned.update(r["excluded"])
        for s in r["fragments"]:owners[s].add(r["id"])
    return dict(ss),meta,{s for s,ids in owners.items() if len(ids)>=2 and s not in banned},banned
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run",type=Path,required=True);a=ap.parse_args();run=a.run.resolve()
    sources,meta,admitted,banned=load(run);c=json.loads((run/"contract.json").read_text())
    expected=set(c["prior_ids"]+c["additional_ids"]);missing=sorted(expected-set(sources))
    if missing:raise ValueError(f"Unsupported frozen targets: {missing}; retain failures, no denominator substitution")
    out=run/"search";out.mkdir();started=time.monotonic()
    bounds={"starts_per_arm":2,"rounds_per_start":4,"trials_per_start":1600,"seconds_per_start":180,"addition_shortlist":24,"removal_shortlist":4,"pair_addition_shortlist":6,"pair_removal_sets":3}
    seed_bounds={"search_seconds_per_arm":120,"shortlist":16,"max_trials_per_arm":4200}
    contract={"schema":"gamma.literal-scale100-search.v1","run_contract_sha256":sha((run/"contract.json").read_bytes()),"pool_sha256":sha((run/"pool.json").read_bytes()),
        "code_hashes":{str(p):sha(p.read_bytes()) for p in [HERE/"search.py",HERE/"pool.cjs",PILOT/"rewrite-v1/search.py",PILOT/"rewrite-v1/fragment-proposals.cjs",PILOT/"joint-v1/search.py",PILOT/"scale-v2/search.py"]},
        "bounds":bounds,"seed_bounds":seed_bounds,"source_style_seeds":["scope","role"],"objective":["selections","package_bytes"],"candidate_policy":"Exact marginal admission; AST<=512bytes plus spans; cross-problem reuse;96ASCII entries; no full entrypoint/body.","total_problems":100,"protected_scoring":False}
    joint.write(run/"search-contract.json",contract)
    seeds=[];records=[];controls=[]
    for width in [7,8]:
        budget=2**width
        for i in range(2):
            p=PILOT/f"rewrite-v1/search-v1/joint-{budget}-start{i}/dictionary.json"
            v=json.loads(p.read_text());assert not set(v)&banned
            seeds.append((f"prior-{budget}-{i}",v))
        p=PILOT/f"scale-v2/search-v2/compact-marginal-{budget}/dictionary.json"
        seeds.append((f"scale-{budget}",json.loads(p.read_text())))
        control=joint.evaluate(sources,seeds[-3][1],width)
        metrics=rw.save(out/f"frozen-{budget}",sources,meta,control,width,"unchanged80-dictionary-on100")
        controls.append({"label":f"frozen-{budget}","metrics":metrics})
    olds,_,_,_=rw.load();oldstyles=rw.styles(olds)
    for style in ["scope","role"]:
        chosen={pid:(oldstyles[style][pid] if pid in olds else style if style in vs else "compact") for pid,vs in sources.items()}
        fixed={pid:{chosen[pid]:sources[pid][chosen[pid]]} for pid in sources}
        texts={str(pid):next(iter(vs.values())) for pid,vs in fixed.items()}
        def proposals(ts,vocab,current):
            ast=rw.ast_rank(fixed,vocab,admitted,8)
            spans=[s for s in rw.old_seed_proposals(ts,vocab,current) if s not in banned][:8]
            return list(dict.fromkeys(ast+spans))
        base.proposals=proposals
        snapshots,trace=base.learn(texts,seed_bounds);joint.write(out/f"{style}-seed-trace.json",trace)
        for budget,(vocab,seqs) in snapshots.items():
            label=f"{style}-learned-{budget}";seeds.append((label,vocab))
            state=joint.evaluate(fixed,vocab,budget.bit_length()-1)
            metrics=rw.save(out/label,sources,meta,state,budget.bit_length()-1,"coherent100-style")
            records.append({"label":label,"metrics":metrics})
        print(json.dumps({"style":style,"seconds":trace["elapsed_seconds"],"trials":trace["exact_candidate_trials"]}),flush=True)
    base.proposals=rw.old_seed_proposals
    def proposals(ss,state,limit):
        return list(dict.fromkeys(rw.ast_rank(ss,state["vocab"],admitted,limit//2)+[s for s in rw.old_proposals(ss,state,limit) if s not in banned][:limit//2]))
    joint.proposals=proposals;screen=[]
    for width in [7,8]:
        states=[]
        for label,vocab in seeds:
            if len(vocab)>2**width:continue
            state=joint.evaluate(sources,vocab,width);state,removed=joint.prune(sources,state,width)
            states.append((label,state));screen.append({"width":width,"seed":label,"score":joint.brief(state),"removed":removed})
        seen=set();chosen=[]
        for label,state in sorted(states,key=lambda x:(joint.cost(x[1],"input"),x[0])):
            key=tuple(state["vocab"])
            if key not in seen:seen.add(key);chosen.append((label,state))
            if len(chosen)==2:break
        for i,(label,state) in enumerate(chosen):
            final,trace=joint.improve(sources,state,width,"input",bounds)
            tag=f"joint-{2**width}-start{i}";metrics=rw.save(out/tag,sources,meta,final,width,"joint100-exact-cost")
            joint.write(out/f"{tag}-trace.json",{"seed":label,"initial_dictionary":state["vocab"],"initial_sources":state["chosen"],"initial":joint.brief(state),**trace});records.append({"label":tag,"seed":label,"metrics":metrics})
            print(json.dumps({"finished":tag,"selections":metrics["selections"],"package_bytes":metrics["package_bytes"]}),flush=True)
    result={"schema":"gamma.literal-scale100-results.v1","problems":100,"source_choices":len(meta),"controls":controls,"records":records,"screen":screen,"elapsed_seconds":time.monotonic()-started,"contract_sha256":sha((run/"search-contract.json").read_bytes()),"scope":"Development representation only;private source/packets retained locally;no independent generalization or automatic selection."}
    joint.write(out/"summary.json",result);print(json.dumps({k:v for k,v in result.items() if k not in ["records","controls","screen"]}))
if __name__=="__main__":main()
