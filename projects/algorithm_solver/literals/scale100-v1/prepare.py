"""Freeze already-qualified development inputs; never changes corpus admission."""
import argparse, hashlib, json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PILOT=HERE.parent
IDS=[54,56,57,59,63,66,71,72,76,77,78,84,85,90,91,93,96,97,128,1512]
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+"\n")
def checked(p,h):
    b=p.read_bytes()
    if sha(b)!=h:raise ValueError(f"Hash mismatch: {p}")
    return b
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--private-root",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
    root=a.private_root.resolve();catalog_path=root/"data/derived/bilingual_development_catalog_v4.json"
    raw=catalog_path.read_bytes();catalog=json.loads(raw)
    reservation=PILOT.parent/"contracts/typed_confirmation_v1.json";reserved=json.loads(reservation.read_text())
    pool=reserved["reservation"]["pool"];aliases={m for r in pool for m in r["members"]}
    existing={r["id"] for r in json.loads((PILOT/"rewrite-v1/proposals.json").read_text())["rows"]}
    assert len(existing)==80 and len(IDS)==20 and not existing.intersection(IDS)
    assert all(f"lcd:{i}" not in aliases and f"doocs:{i:04d}" not in aliases for i in IDS)
    a.output.mkdir(parents=True,exist_ok=False);(a.output/"inputs").mkdir()
    rows=[]
    for pid in IDS:
        row=next(r for r in catalog["rows"] if r["id"]==pid)
        impl=next(r for r in row["implementations"] if r["language"]=="javascript")
        assert impl["qualified"] is True
        source=checked(root/impl["source"],impl["source_sha256"])
        receipt_path=root/impl["qualification_receipt"];receipt_raw=receipt_path.read_bytes()
        if impl.get("qualification_receipt_sha256"):assert sha(receipt_raw)==impl["qualification_receipt_sha256"]
        receipt=json.loads(receipt_raw);metadata=receipt.get("independent_test_sets",receipt.get("test_metadata",[]))
        extra={}
        if pid==1512:
            seal_path=root/"runs/source-corpus-js-py-128-v2/source-seal.json";seal_raw=seal_path.read_bytes()
            seal=next(r for r in json.loads(seal_raw) if r["uid"]=="lcd:1512")
            assert seal["sources"]["javascript-normalized"]["sha256"]==impl["source_sha256"]
            metadata=[{"absolute_path":str(root/"data/derived/tests/lcd__1512.json"),"sha256":seal["independent_tests_sha256"]}]
            extra={"source_seal_path":str(seal_path),"source_seal_sha256":sha(seal_raw),"domain":seal["domain"],"provenance":seal["source_provenance"]}
        assert metadata
        tests=[]
        for m in metadata:
            part=json.loads(Path(m["absolute_path"]).read_bytes())
            assert sha(json.dumps(part,sort_keys=True,separators=None if pid==1512 else (",",":"),ensure_ascii=False).encode())==m["sha256"], "canonical test identity"
            tests.extend(part)
        assert len(tests)==impl["independent_cases"] and all(set(t)<= {"args","expected","compare"} and t.get("compare","return")=="return" for t in tests)
        semantics=None
        if impl.get("semantics"):
            semantics=json.loads(checked(root/impl["semantics"],impl["semantics_sha256"]))
        test_file=f"inputs/{pid:04d}-tests.json";source_file=f"inputs/{pid:04d}.js"
        (a.output/source_file).write_bytes(source);write(a.output/test_file,tests)
        mode="return"
        if pid in [78,90]:
            e=impl["evaluation_contract"];assert e["comparison"]=="return:unordered_outer"
            checked(root/e["path"],e["sha256"]);checked(root/e["comparator_path"],e["comparator_sha256"])
            mode=e["comparison"]
        rows.append({"id":pid,"key":row["key"],"source_file":source_file,"source_sha256":sha(source),
            "test_file":test_file,"test_sha256":sha((a.output/test_file).read_bytes()),"cases":len(tests),
            "compare":mode,"original_test_metadata":metadata,"historical_test_hash_encoding":"sorted-default-json" if pid==1512 else "sorted-compact-json","semantics":semantics,"catalog_implementation":impl,"receipt_sha256":sha(receipt_raw),"extra":extra})
    contract={"schema":"gamma.literal-scale100-contract.v1","host":"128","scope":"100 exposed development problems: previous80 plus20 already-qualified inputs. Representation only; no admission, protected scoring, model training or autonomous claim.",
        "prior_ids":sorted(existing),"additional_ids":IDS,"prior_source_pool_sha256":sha((PILOT/"rewrite-v1/proposals.json").read_bytes()),
        "catalog_sha256":sha(raw),"reservation_sha256":sha(reservation.read_bytes()),"protected_overlap":[],
        "source_policy":"Only entrypoint normalization, printing, capture-checked renaming and existing guarded arrow transform. Preserve outputs, mutation and return aliases. No algorithm replacement.",
        "comparison_policy":"Retain every assigned independent test. Original receipt's comparator: outer order only for78/90; otherwise existing return comparator. Also require exact original output, input effects and alias topology.",
        "cost_policy":"128/256 flat exact strings;96 counted ASCII/newline entries, no whole entrypoints/bodies, >=2 problem owners for multichar entries. Include packet headers and dictionary.",
        "privacy":"Raw sources, tests, dictionaries and packets incorporating private code stay in ignored output. Publish code, hashes and aggregate receipts only.",
        "limits":{"max_new_sources":140,"qualification_seconds":180,"search_seconds_per_arm":180,"max_artifact_bytes":134217728,"workers":1,"batch_cases":16,"sandbox_cpu_seconds":3,"sandbox_wall_seconds":8,"output_bytes":4194304},
        "rows":rows,"code_hashes":{p.name:sha(p.read_bytes()) for p in HERE.iterdir() if p.suffix in [".py",".cjs"]}}
    write(a.output/"contract.json",contract)
    print(json.dumps({"frozen_problems":100,"new_problems":len(rows),"new_independent_cases":sum(r["cases"] for r in rows),"contract_sha256":sha((a.output/"contract.json").read_bytes())}))
if __name__=="__main__":main()
