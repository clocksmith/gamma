"""Compare a qualified semantic refactor with unchanged literal dictionaries."""
import argparse,hashlib,importlib.util,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PILOT=ROOT.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rw=module("heap_search",PILOT/"rewrite-v1/search.py")
audit=module("heap_audit",PILOT/"joint-v1/audit.py")
scale=module("heap_scale100",PILOT/"scale100-v1/search.py")
def main():
    p=argparse.ArgumentParser();p.add_argument("--prior-run",type=Path,required=True);p.add_argument("--private-output",type=Path,required=True);a=p.parse_args()
    contract=json.loads((ROOT/"contract.json").read_text())
    for rel,h in contract["inputs"].items():assert sha((ROOT/rel).read_bytes())==h
    q=json.loads((ROOT/"qualification/report.json").read_text());m=json.loads((ROOT/"generated/manifest.json").read_text())
    assert q["generated_manifest_sha256"]==sha((ROOT/"generated/manifest.json").read_bytes())
    assert m["contract_sha256"]==sha((ROOT/"contract.json").read_bytes()) and m["generator_sha256"]==sha((ROOT/"generate.cjs").read_bytes())
    assert q["source_count"]==q["passed_sources"]==4
    for row in q["rows"]:
        assert row["passed"] and not row["failures"] and sha((ROOT/"generated"/row["file"]).read_bytes())==row["sha256"]
        for k,call in enumerate(row["calls"]):
            for suffix in ["stdout","stderr"]:
                path=ROOT/"qualification/observations"/f"1046-{row['variant']}-{k*256}.{suffix}"
                assert sha(path.read_bytes())==call[suffix+"_sha256"]
    prior_evidence=json.loads((PILOT/"scale100-v1/evidence/audit.json").read_text())
    assert sha((a.prior_run/"contract.json").read_bytes())==prior_evidence["contract_sha256"]
    assert sha((a.prior_run/"qualification/report.json").read_bytes())==prior_evidence["qualification_sha256"]
    sources,metadata,admitted,banned=scale.load(a.prior_run)
    assert len(sources)==100
    new_sources={r["variant"]:(ROOT/"generated"/r["file"]).read_text() for r in q["rows"] if r["variant"]!="original"}
    for row in q["rows"]:
        if row["variant"]!="original":metadata[1046,row["variant"]]={**row,"file":str((ROOT/"generated"/row["file"]).resolve())}
    original_pool={pid:dict(vs) for pid,vs in sources.items()}
    sources[1046].update(new_sources)
    a.private_output.mkdir(exist_ok=False);out=ROOT/"encodings";out.mkdir()
    records=[];count=0
    for width in [7,8]:
        budget=2**width;vocab=json.loads((PILOT/f"rewrite-v1/search-v1/joint-{budget}-start0/dictionary.json").read_text())
        before=rw.joint.evaluate(original_pool,vocab,width);after=rw.joint.evaluate(sources,vocab,width)
        for variant,text in new_sources.items():
            state=rw.joint.evaluate({1046:{variant:text}},vocab,width)
            folder=out/f"{variant}-{width}";metrics=rw.save(folder,{1046:{variant:text}},metadata,state,width,"new-source-frozen-dictionary")
            manifest=json.loads((folder/"manifest.json").read_text());record=manifest["programs"][0]
            decoded,words,seq,w=audit.packet_audit.unpack((folder/"dictionary.ltd").read_bytes(),(folder/"1046.ltv").read_bytes())
            assert decoded==text and seq==record["sequence"] and len(seq)==audit.minimum_count(text,words)
            count+=1;records.append({"variant":variant,"width":width,"source_sha256":sha(text.encode()),"metrics":metrics})
        label=f"full100-{budget}"
        metrics=rw.save(a.private_output/label,sources,metadata,after,width,"single-semantic-refactor-frozen-dictionary")
        exact,chosen=audit.score(sources,vocab,width)
        for k,v in exact.items():assert metrics[k]==v
        manifest=json.loads((a.private_output/label/"manifest.json").read_text());folder=a.private_output/label
        for r in manifest["programs"]:
            packet=(folder/f"{r['id']}.ltv").read_bytes()
            decoded,words,seq,w=audit.packet_audit.unpack((folder/"dictionary.ltd").read_bytes(),packet)
            assert sha(packet)==r["packet_sha256"] and sha(decoded.encode())==r["source_sha256"]
            assert decoded==sources[r["id"]][r["variant"]] and seq==r["sequence"] and len(seq)==audit.minimum_count(decoded,words)
            count+=1
        records.append({"label":label,"width":width,"before":rw.joint.brief(before),"after":metrics,
                        "chosen1046":after["chosen"][1046],"old1046_selections":len(before["parsed"][(1046,before["chosen"][1046])]),
                        "new1046_selections":len(after["parsed"][(1046,after["chosen"][1046])])})
    result={"schema":"gamma.literal-heap-comparison.v1","host":"128","scope":"Same100 consumed development problems; frozen dictionaries, one semantic source refactor. No autonomous/generalization claim.",
        "checks_total":q["checks_total"],"checks_passed":q["checks_passed"],"distinct_cases":q["distinct_cases"],
        "records":records,"packets_independently_decoded":count,"contract_sha256":sha((ROOT/"contract.json").read_bytes()),
        "qualification_sha256":sha((ROOT/"qualification/report.json").read_bytes()),"measurement_sha256":sha(Path(__file__).read_bytes()),
        "private_full100_packages":str(a.private_output.resolve()),"public_packets":"encodings/ contains only public1046 refactors and previously public dictionaries"}
    (ROOT/"summary.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps({k:v for k,v in result.items() if k!="records"}))
    for r in records:
        if "label" in r:print(json.dumps(r))
if __name__=="__main__":main()
