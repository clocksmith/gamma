"""Independent packet/segmentation audit; publish hashes and metrics, not private code."""
import argparse, hashlib, importlib.util, json, math, statistics
from collections import defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent;PILOT=HERE.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
prior=load_module("scale100_packet_audit",PILOT/"joint-v1/audit.py")
def write(p,d):p.write_text(json.dumps(d,indent=2)+"\n")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run",type=Path,required=True);ap.add_argument("--publish",type=Path,required=True);a=ap.parse_args()
    run=a.run.resolve();c=json.loads((run/"contract.json").read_text());sc=json.loads((run/"search-contract.json").read_text())
    assert sc["run_contract_sha256"]==sha((run/"contract.json").read_bytes())
    for name,h in c["code_hashes"].items():assert sha((HERE/name).read_bytes())==h,name
    for path,h in sc["code_hashes"].items():assert sha(Path(path).read_bytes())==h,path
    assert sc["pool_sha256"]==sha((run/"pool.json").read_bytes())
    q=json.loads((run/"qualification/report.json").read_text());m=json.loads((run/"generated/manifest.json").read_text())
    assert q["contract_sha256"]==sha((run/"contract.json").read_bytes())==m["contract_sha256"]
    assert q["generated_manifest_sha256"]==sha((run/"generated/manifest.json").read_bytes())
    assert q["harness_sha256"]==sha((HERE/"harness.cjs").read_bytes())
    qnew={(r["id"],r["variant"]):r for r in q["rows"]}
    oldbase=PILOT/"rewrite-v1";qold={(r["id"],r["variant"]):r for r in json.loads((oldbase/"qualification/report.json").read_text())["rows"]}
    scale=PILOT/"scale-v2";qscale={(r["id"],"old-"+r["variant"]):r for r in json.loads((scale/"qualification/report.json").read_text())["rows"]}
    for r in q["rows"]:
        assert sha((run/"generated"/r["file"]).read_bytes())==r["sha256"]
        for call in r["calls"]:
            for ext in ["stdout","stderr"]:assert sha((run/"qualification/observations"/(call["stem"]+"."+ext)).read_bytes())==call[ext+"_sha256"]
    pool=json.loads((run/"pool.json").read_text());assert pool["qualification_sha256"]==sha((run/"qualification/report.json").read_bytes())
    assert pool["generator_sha256"]==sha((HERE/"pool.cjs").read_bytes())
    sources=defaultdict(dict);metadata={};banned=set();inventory=[]
    for r in pool["rows"]:
        text=Path(r["file"]).read_text();key=(r["id"],r["variant"])
        verdict=(qnew if r["receipt_kind"]=="new20" else qscale if r["variant"].startswith("old-") else qold)[key]
        assert sha(text.encode())==r["sha256"]==verdict["sha256"] and verdict["passed"] and not verdict["failures"]
        sources[r["id"]][r["variant"]]=text;metadata[key]=r;banned.update(r["excluded"])
        inventory.append({"id":r["id"],"variant":r["variant"],"source_sha256":r["sha256"],"receipt_kind":r["receipt_kind"],"checks":verdict["checks_total"]})
    assert set(sources)==set(c["prior_ids"]+c["additional_ids"]) and len(sources)==100
    summary=json.loads((run/"search/summary.json").read_text());assert summary["contract_sha256"]==sha((run/"search-contract.json").read_bytes())
    packets=0;moves=0;records=[]
    for mp in sorted((run/"search").glob("*/manifest.json")):
        manifest=json.loads(mp.read_text());metrics=manifest["metrics"];folder=mp.parent;raw=(folder/"dictionary.ltd").read_bytes()
        assert sha(raw)==manifest["dictionary_sha256"];counts=[];single=0;size=0;byproblem=[];seen=set()
        for r in manifest["programs"]:
            packed=(folder/f"{r['id']}.ltv").read_bytes();assert sha(packed)==r["packet_sha256"]
            text,vocab,seq,width=prior.packet_audit.unpack(raw,packed);key=(r["id"],r["variant"])
            assert text==sources[key[0]][key[1]] and sha(text.encode())==r["source_sha256"]==metadata[key]["sha256"]
            assert r["source_file"]==metadata[key]["file"] and r["entry"]=="solve" and r["interface"]=="named-function"
            assert seq==r["sequence"] and len(seq)==r["selections"]==prior.minimum_count(text,vocab)
            assert len(seq)*width==r["selection_bits"] and width==metrics["bits_per_selection"]
            assert r["id"] not in seen;seen.add(r["id"]);packets+=1;counts.append(len(seq));size+=len(packed)
            fallback=sum(len(vocab[i])==1 for i in seq);single+=fallback
            byproblem.append({"id":r["id"],"variant":r["variant"],"selections":len(seq),"character_selections":fallback,"source_sha256":r["source_sha256"]})
        assert seen==set(sources) and len(vocab)<=2**width and len(vocab)==metrics["entries"]
        assert not set(vocab)&banned
        assert set(chr(i) for i in range(32,127))|{"\n"}<=set(vocab)
        for s in vocab:
            assert len(s.encode())<=512
            if len(s)>1:assert sum(any(s in t for t in vs.values()) for vs in sources.values())>=2
        assert sum(counts)==metrics["selections"] and single==metrics["single_character_selections"]
        assert single/sum(counts)==metrics["single_character_selection_fraction"]
        assert statistics.median(counts)==metrics["median_selections"] and max(counts)==metrics["worst_selections"]
        assert sorted(counts)[math.ceil(.95*len(counts))-1]==metrics["p95_selections"]
        assert len(raw)==metrics["dictionary_bytes"] and size==metrics["packet_bytes"] and size+len(raw)==metrics["package_bytes"]
        if folder.name.startswith(("joint-","frozen-")):
            exact,chosen=prior.score(sources,vocab,width)
            for k,v in exact.items():assert metrics[k]==v
            assert {r["id"]:(r["variant"],r["selections"]) for r in manifest["programs"]}==chosen
        if folder.name.startswith("joint-"):
            trace=json.loads((run/"search"/(folder.name+"-trace.json")).read_text())
            current=set(trace["initial_dictionary"]);before,_=prior.score(sources,current,width);assert before==trace["initial"]
            for step in trace["rounds"]:
                assert step["before"]==before
                if step["accepted"]:
                    move=step["accepted"];current.difference_update(move["remove"]);current.update(move["add"])
                    actual,_=prior.score(sources,current,width);assert actual==move["result"]
                    current.difference_update(step["pruned_after_move"]);after,_=prior.score(sources,current,width)
                    assert (after["selections"],after["package_bytes"])<(before["selections"],before["package_bytes"])
                    moves+=1;before=after
                assert before==step["after"]
            assert current==set(vocab)
        groups={}
        for label,ids in [("previous80",c["prior_ids"]),("new20",c["additional_ids"])]:
            selected=[r for r in byproblem if r["id"] in ids];counts2=sorted(r["selections"] for r in selected);total=sum(counts2)
            groups[label]={"problems":len(selected),"selections":total,"median":statistics.median(counts2),"p95":counts2[math.ceil(.95*len(counts2))-1],"character_fraction":sum(r["character_selections"] for r in selected)/total}
        records.append({"label":folder.name,"metrics":metrics,"groups":groups,"program_costs":byproblem,"dictionary_sha256":sha(raw),"manifest_sha256":sha(mp.read_bytes())})
    byte_count=sum(p.stat().st_size for p in run.rglob("*") if p.is_file());assert byte_count<c["limits"]["max_artifact_bytes"]
    result={"schema":"gamma.literal-scale100-audit.v1","host":"128","passed":True,"total_problems":100,"prior_problems_reusing_execution":80,
        "new_problems":20,"qualified_source_choices":len(metadata),"new_source_versions":q["source_count"],"new_sources_passed":q["passed_sources"],
        "new_checks_total":q["checks_total"],"new_checks_passed":q["checks_passed"],"new_distinct_cases":q["distinct_cases"],
        "total_distinct_development_cases":8412+q["distinct_cases"],"qualification_seconds":q["elapsed_seconds"],"search_seconds":summary["elapsed_seconds"],
        "packets_independently_decoded":packets,"accepted_moves_replayed":moves,"artifact_bytes":byte_count,"comparisons":records,
        "contract_sha256":sha((run/"contract.json").read_bytes()),"search_contract_sha256":sha((run/"search-contract.json").read_bytes()),
        "source_manifest_sha256":sha((run/"generated/manifest.json").read_bytes()),"qualification_sha256":sha((run/"qualification/report.json").read_bytes()),
        "private_run_path":str(run),"scope":"100 consumed development problems. Qualification means finite existing tests plus original parity; no maximum-bound, autonomous or protected claim.",
        "audit_sha256":sha(Path(__file__).read_bytes())}
    a.publish.mkdir(exist_ok=False)
    write(a.publish/"audit.json",result)
    # No source strings, statements, expected values, dictionaries or sequences.
    public_c={k:v for k,v in c.items() if k!="rows"}
    public_c["problems"]=[{k:r[k] for k in ["id","key","source_sha256","test_sha256","cases","compare","receipt_sha256","historical_test_hash_encoding"]} for r in c["rows"]]
    write(a.publish/"contract-summary.json",public_c);write(a.publish/"source-inventory.json",inventory)
    write(a.publish/"search-contract.json",sc)
    failures=[]
    for p in sorted(run.parent.glob("literal-100-v*/preparation-failure.json")):failures.append({"path":str(p),"sha256":sha(p.read_bytes()),**json.loads(p.read_text())})
    write(a.publish/"preparation-failures.json",failures)
    print(json.dumps({k:v for k,v in result.items() if k not in ["comparisons"]}))
if __name__=="__main__":main()
