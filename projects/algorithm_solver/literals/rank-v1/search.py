"""Matched estimated versus actual marginal ranking of one bounded proposal pool."""
import argparse,hashlib,importlib.util,json,math,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PILOT=ROOT.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def module(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rw=module("rank_rw",PILOT/"rewrite-v1/search.py");joint=rw.joint
scale=module("rank_load",PILOT/"scale100-v1/search.py")
audit=module("rank_audit",PILOT/"joint-v1/audit.py")
def exact_add(sources,state,fragment,width):
    """Permit temporary overflow for ranking only; every admitted move is budgeted."""
    tree=rw.base.trie([*state["vocab"],fragment]);counts=[]
    for pid,vs in sources.items():
        counts.append(min(len(rw.base.segment(t,tree)) if fragment in t else len(state["parsed"][pid,v]) for v,t in vs.items()))
    dictionary=state["dictionary_bytes"]+4+len(fragment.encode())
    return {"selections":sum(counts),"package_bytes":dictionary+sum(41+(width*n+7)//8 for n in counts)}
def estimated(sources,state,fragment):
    saving=len(rw.base.segment(fragment,rw.base.trie(state["vocab"])))-1
    return saving*sum(max(t.count(fragment) for t in vs.values()) for vs in sources.values())
def main():
    p=argparse.ArgumentParser();p.add_argument("--parent",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    parent=a.parent.resolve();out=a.output.resolve();out.mkdir(exist_ok=False)
    verified=json.loads((PILOT/"row-v1/evidence/audit.json").read_text())
    assert verified["passed"] and verified["summary_sha256"]==sha((parent/"search/summary.json").read_bytes())
    pc=json.loads((parent/"search-contract.json").read_text())
    assert sha((parent/"pool.json").read_bytes())==pc["pool_sha256"]
    assert sha((parent/"search-contract.json").read_bytes())==verified["search_contract_sha256"]
    ss,meta,admitted,banned=scale.load(parent)
    # New source bytes are forbidden in this experiment.
    inventory={(r["id"],r["variant"]):r["source_sha256"] for r in json.loads((PILOT/"scale100-v1/evidence/source-inventory.json").read_text())}
    for folder in [PILOT/"heap-v1",parent]:
        for r in json.loads((folder/"qualification/report.json").read_text())["rows"]:
            if r["variant"]!="original":inventory[r["id"],r["variant"]]=r["sha256"]
    for key,r in meta.items():assert r["sha256"]==inventory[key]
    limits={"rounds_per_start":4,"trials_per_start":1600,"seconds_per_start":120,"addition_shortlist":24,"removal_shortlist":4,"pair_addition_shortlist":6,"pair_removal_sets":3}
    contract={"schema":"gamma.literal-marginal-rank.v1","parent_commit":"e3d17ddfbadc3b5483dc151fd58cea4850027d2d","parent_audit_sha256":sha((PILOT/"row-v1/evidence/audit.json").read_bytes()),"pool_sha256":pc["pool_sha256"],
      "source_choices":len(meta),"problems":100,"limits":limits,"proposal_pool":{"ast":192,"encoded_spans":192},"routes":["estimated","exact"],
      "ranking":"Same bounded pool per visited state; estimated occurrence saving versus complete resegmentation with source reselection. Over-cap additions are ranking probes, never admitted packets.",
      "objective":["selections","package_bytes"],"scope":"Dictionary search only; unchanged qualified source bytes; no model, admission or protected work.",
      "code_hashes":{str(p):sha(p.read_bytes()) for p in [ROOT/"search.py",PILOT/"rewrite-v1/search.py",PILOT/"joint-v1/search.py",PILOT/"joint-v1/audit.py",PILOT/"scale-v2/audit.py",PILOT/"scale-v2/search.py",PILOT/"scale100-v1/search.py"]},
      "seeds":{str(w):{"file":str(parent/f"search/joint-{2**w}/dictionary.json"),"sha256":sha((parent/f"search/joint-{2**w}/dictionary.json").read_bytes())} for w in [7,8]}}
    joint.write(out/"contract.json",contract);records=[];all_start=time.monotonic()
    for w in [7,8]:
        vocab=json.loads(Path(contract["seeds"][str(w)]["file"]).read_text());initial=joint.evaluate(ss,vocab,w)
        for route in ["estimated","exact"]:
            rankings=[];rank_seconds=0.
            def proposals(s,state,limit):
                nonlocal rank_seconds
                start=time.monotonic()
                pool=list(dict.fromkeys(rw.ast_rank(s,state["vocab"],admitted,192)+[x for x in rw.old_proposals(s,state,192) if x not in banned]))
                estimates={f:estimated(s,state,f) for f in pool}
                actual={f:exact_add(s,state,f,w) for f in pool} if route=="exact" else {}
                chosen=sorted(pool,key=(lambda f:(actual[f]["selections"],actual[f]["package_bytes"],f)) if route=="exact" else (lambda f:(-estimates[f],len(f.encode()),f)))[:limit]
                rank_seconds+=time.monotonic()-start
                rankings.append({"before":joint.brief(state),"candidates":[{"fragment":f,"estimate":estimates[f],**({"actual_add":actual[f]} if f in actual else {})} for f in pool],"selected":chosen})
                return chosen
            joint.proposals=proposals
            final,trace=joint.improve(ss,initial,w,"input",limits)
            label=f"{route}-{2**w}";metrics=rw.save(out/label,ss,meta,final,w,route+"-marginal-ranking")
            joint.write(out/f"{label}-trace.json",{"initial_dictionary":initial["vocab"],"initial":joint.brief(initial),**trace,"rankings":rankings})
            # Separate forward DP audit; source identities already joined above.
            exact,chosen=audit.score(ss,final["vocab"],w)
            for k,v in exact.items():assert metrics[k]==v
            manifest=json.loads((out/label/"manifest.json").read_text());counts=[];single=0
            program_costs=[]
            for r in manifest["programs"]:
                packet=(out/label/f"{r['id']}.ltv").read_bytes()
                decoded,words,seq,width=audit.packet_audit.unpack((out/label/"dictionary.ltd").read_bytes(),packet)
                assert decoded==ss[r["id"]][r["variant"]] and sha(decoded.encode())==meta[r["id"],r["variant"]]["sha256"]==r["source_sha256"]
                assert sha(packet)==r["packet_sha256"] and seq==r["sequence"] and len(seq)==audit.minimum_count(decoded,words)
                assert width==w and chosen[r["id"]]==(r["variant"],len(seq))
                n=sum(len(words[i])==1 for i in seq);single+=n;counts.append(len(seq))
                program_costs.append({"id":r["id"],"variant":r["variant"],"selections":len(seq),"character_selections":n,"source_sha256":r["source_sha256"]})
            assert single==metrics["single_character_selections"] and single/sum(counts)==metrics["single_character_selection_fraction"]
            assert statistics.median(counts)==metrics["median_selections"] and sorted(counts)[math.ceil(.95*len(counts))-1]==metrics["p95_selections"]
            assert not set(words)&banned
            for f in words:
                if len(f)>1:assert sum(any(f in t for t in vs.values()) for vs in ss.values())>=2
            current=set(initial["vocab"]);before,_=audit.score(ss,current,w);moves=0
            for step in trace["rounds"]:
                assert before==step["before"]
                if step["accepted"]:
                    move=step["accepted"];current.difference_update(move["remove"]);current.update(move["add"])
                    actual,_=audit.score(ss,current,w);assert actual==move["result"]
                    current.difference_update(step["pruned_after_move"]);before,_=audit.score(ss,current,w);moves+=1
                assert before==step["after"]
            assert current==set(final["vocab"])
            record={"label":label,"metrics":metrics,"initial":joint.brief(initial),"trials":trace["trials"],"stop":trace["stop"],"elapsed_seconds":trace["elapsed_seconds"],"ranking_seconds":rank_seconds,
              "ranking_probes":sum(len(r["candidates"]) for r in rankings) if route=="exact" else 0,"packets_independently_decoded":len(manifest["programs"]),"accepted_moves_independently_replayed":moves,
              "program_costs":program_costs,"manifest_sha256":sha((out/label/"manifest.json").read_bytes()),"trace_sha256":sha((out/f"{label}-trace.json").read_bytes())}
            records.append(record);joint.write(out/"progress.json",records)
            print(json.dumps({k:v for k,v in record.items() if k not in ["program_costs","metrics"]}|{"metrics":metrics}),flush=True)
    joint.write(out/"report.json",{"schema":"gamma.literal-marginal-rank-results.v1","passed":True,"host":"128","records":records,"elapsed_seconds":time.monotonic()-all_start,"contract_sha256":sha((out/"contract.json").read_bytes()),"source_pool_sha256":pc["pool_sha256"],"private_run":str(out),"qualification":"No source changed; reuse hash-bound native receipts from row-v1,heap-v1,scale100-v1. Independent packet and forward-segmentation checks executed here.","scope":contract["scope"]})
if __name__=="__main__":main()
