"""Independent source/receipt joins, forward segmentation and accepted-move replay."""
import argparse,hashlib,importlib.util,json,math,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PILOT=ROOT.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def module(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
prior=module("row_independent",PILOT/"joint-v1/audit.py")
def write(p,x):p.write_text(json.dumps(x,indent=2)+"\n")
def main():
    p=argparse.ArgumentParser();p.add_argument("--run",type=Path,required=True);p.add_argument("--publish",type=Path,required=True);a=p.parse_args();run=a.run.resolve()
    c=json.loads((run/"contract.json").read_text());sc=json.loads((run/"search-contract.json").read_text())
    for contract in [c,sc]:
        for file,h in contract["code_hashes"].items():assert sha(Path(file).read_bytes())==h,file
    for seed in sc["seeds"].values():assert sha(Path(seed["file"]).read_bytes())==seed["sha256"]
    assert sha((run/"pool.json").read_bytes())==sc["pool_sha256"]
    pool=json.loads((run/"pool.json").read_text())
    assert pool["builder_sha256"]==sha((ROOT/"pool.cjs").read_bytes())
    assert pool["contract_sha256"]==sha((run/"contract.json").read_bytes())
    q=json.loads((run/"qualification/report.json").read_text())
    assert q["contract_sha256"]==sha((run/"contract.json").read_bytes())
    assert q["generated_manifest_sha256"]==sha((run/"generated/manifest.json").read_bytes())
    assert q["harness_sha256"]==sha((ROOT/"harness.cjs").read_bytes())
    assert sha((run/"qualification/report.json").read_bytes())==sc["qualification_sha256"]
    inv={(r["id"],r["variant"]):r for r in json.loads((PILOT/"scale100-v1/evidence/source-inventory.json").read_text())}
    base_audit=json.loads((PILOT/"scale100-v1/evidence/audit.json").read_text())
    old=Path(c["prior_run"])
    assert sha((old/"contract.json").read_bytes())==base_audit["contract_sha256"]
    assert sha((old/"qualification/report.json").read_bytes())==base_audit["qualification_sha256"]
    assert sha((old/"pool.json").read_bytes())==c["prior_pool_sha256"]
    for receipt in pool["receipts"]:assert sha(Path(receipt["report"]).read_bytes())==receipt["sha256"]
    for folder in [PILOT/"heap-v1",run]:
        r=json.loads((folder/"qualification/report.json").read_text())
        for row in r["rows"]:
            assert row["passed"] and not row["failures"] and row["checks_passed"]==row["checks_total"]
            assert sha((folder/"generated"/row["file"]).read_bytes())==row["sha256"]
            if row["variant"]!="original":inv[row["id"],row["variant"]]={"source_sha256":row["sha256"],"checks":row["checks_total"]}
            for i,call in enumerate(row["calls"]):
                stem=call.get("stem",f"1046-{row['variant']}-{i*256}")
                for ext in ["stdout","stderr"]:assert sha((folder/"qualification/observations"/(stem+"."+ext)).read_bytes())==call[ext+"_sha256"]
    sources=defaultdict(dict);metadata={};banned=set()
    for r in pool["rows"]:
        key=(r["id"],r["variant"]);text=Path(r["file"]).read_text()
        assert sha(text.encode())==r["sha256"]==inv[key]["source_sha256"]
        assert key not in metadata
        sources[r["id"]][r["variant"]]=text;metadata[key]=r;banned.update(r["excluded"])
    assert len(sources)==100
    old_sources={pid:{v:t for v,t in vs.items() if not v.startswith("row-")} for pid,vs in sources.items()}
    summary=json.loads((run/"search/summary.json").read_text());assert summary["contract_sha256"]==sha((run/"search-contract.json").read_bytes())
    results=[];packets=0;moves=0
    for record in summary["records"]:
        folder=run/"search"/record["label"];mp=folder/"manifest.json";m=json.loads(mp.read_text())
        assert sha(mp.read_bytes())==record["manifest_sha256"] and m["metrics"]==record["metrics"]
        metrics=m["metrics"];w=metrics["bits_per_selection"];raw=(folder/"dictionary.ltd").read_bytes()
        assert sha(raw)==m["dictionary_sha256"]
        current_sources=old_sources if record["label"].startswith(("baseline-","dictionary-only-")) else sources
        rows=[];owners=defaultdict(set);seen=set();size=0
        for r in m["programs"]:
            packet=(folder/f"{r['id']}.ltv").read_bytes()
            text,vocab,seq,width=prior.packet_audit.unpack(raw,packet);key=(r["id"],r["variant"])
            assert sha(packet)==r["packet_sha256"]
            assert text==current_sources[key[0]][key[1]] and sha(text.encode())==r["source_sha256"]==metadata[key]["sha256"]
            assert r["source_file"]==metadata[key]["file"] and r["entry"]=="solve" and r["interface"]=="named-function"
            assert seq==r["sequence"] and len(seq)==r["selections"]==prior.minimum_count(text,vocab)
            assert width==w and len(seq)*w==r["selection_bits"]
            assert r["id"] not in seen;seen.add(r["id"]);size+=len(packet);packets+=1
            for i in set(seq):owners[i].add(r["id"])
            rows.append({"id":r["id"],"variant":r["variant"],"selections":len(seq),"character_selections":sum(len(vocab[i])==1 for i in seq),"source_sha256":r["source_sha256"]})
        assert seen==set(sources) and len(vocab)<=2**w and len(vocab)==metrics["entries"]
        assert not set(vocab)&banned and not set(vocab)&{t for vs in sources.values() for t in vs.values()}
        assert set(chr(i) for i in range(32,127))|{"\n"}<=set(vocab)
        for s in vocab:
            assert len(s.encode())<=512
            if len(s)>1:assert sum(any(s in t for t in vs.values()) for vs in sources.values())>=2
        counts=sorted(r["selections"] for r in rows);single=sum(r["character_selections"] for r in rows)
        assert sum(counts)==metrics["selections"] and single==metrics["single_character_selections"]
        assert single/sum(counts)==metrics["single_character_selection_fraction"]
        assert statistics.median(counts)==metrics["median_selections"] and max(counts)==metrics["worst_selections"]
        assert counts[math.ceil(.95*len(counts))-1]==metrics["p95_selections"]
        assert len(raw)==metrics["dictionary_bytes"] and size==metrics["packet_bytes"] and size+len(raw)==metrics["package_bytes"]
        exact,chosen=prior.score(current_sources,vocab,w)
        for k,v in exact.items():assert metrics[k]==v
        assert chosen=={r["id"]:(r["variant"],r["selections"]) for r in m["programs"]}
        if record["label"].startswith("joint-"):
            trace=json.loads((run/f"search/trace-{w}.json").read_text());current=set(trace["initial_dictionary"])
            before,_=prior.score(sources,current,w);assert before==trace["initial"]
            for step in trace["rounds"]:
                assert step["before"]==before
                if step["accepted"]:
                    move=step["accepted"];current.difference_update(move["remove"]);current.update(move["add"])
                    actual,_=prior.score(sources,current,w);assert actual==move["result"]
                    current.difference_update(step["pruned_after_move"]);after,_=prior.score(sources,current,w)
                    assert (after["selections"],after["package_bytes"])<(before["selections"],before["package_bytes"])
                    moves+=1;before=after
                assert step["after"]==before
            assert current==set(vocab)
        inventory=[{"index":i,"bytes":len(s.encode()),"sha256":sha(s.encode()),"selected_problem_ids":sorted(owners[i])} for i,s in enumerate(vocab) if s.startswith("function h(")]
        results.append({"label":record["label"],"metrics":metrics,"program_costs":rows,"helper_literals":inventory,"manifest_sha256":sha(mp.read_bytes()),"dictionary_sha256":sha(raw)})
    byte_count=sum(p.stat().st_size for p in run.rglob("*") if p.is_file());assert byte_count<c["limits"]["max_artifact_bytes"]
    result={"schema":"gamma.literal-row-audit.v1","passed":True,"host":"128","total_problems":100,"new_source_versions":q["source_count"],"checks_passed":q["checks_passed"],"checks_total":q["checks_total"],"distinct_cases":q["distinct_cases"],"qualified_source_choices":len(metadata),"packets_independently_decoded":packets,"accepted_moves_replayed":moves,"qualification_seconds":q["elapsed_seconds"],"search_seconds":summary["elapsed_seconds"],"artifact_bytes":byte_count,"comparisons":results,
      "contract_sha256":sha((run/"contract.json").read_bytes()),"search_contract_sha256":sha((run/"search-contract.json").read_bytes()),"qualification_sha256":sha((run/"qualification/report.json").read_bytes()),"source_manifest_sha256":sha((run/"generated/manifest.json").read_bytes()),"summary_sha256":sha((run/"search/summary.json").read_bytes()),"private_run_path":str(run),"audit_sha256":sha(Path(__file__).read_bytes()),
      "scope":"Finite development execution plus original effect/type parity; independent source receipt join and exact segmentation. No maximum-input performance, autonomous or protected result."}
    a.publish.mkdir(exist_ok=False);write(a.publish/"audit.json",result)
    write(a.publish/"contract-summary.json",c);write(a.publish/"search-contract.json",sc)
    write(a.publish/"sources.json",[{"id":r["id"],"variant":r["variant"],"sha256":r["sha256"],"checks":r["checks_total"],"passed":r["passed"],"failures":r["failures"]} for r in q["rows"]])
    print(json.dumps({k:v for k,v in result.items() if k!="comparisons"}))
if __name__=="__main__":main()
