"""Read-only fit-input tokenizer check; never allocate model or train."""
import json
from pathlib import Path
from transformers import AutoTokenizer
from algsolve.embed import EMBEDDING_DIR, verify_weights
from algsolve.records import LANE_ROOT as ROOT
from algsolve.rebuild_recognition import sha, publish
from algsolve.synth import typed_codec, typed_confirmation
from algsolve.synth.train_typed import query_text, INSTRUCTION
OUT=ROOT/'findings/typed-literal-objective-proposal-128-v1'

def main():
    assert not (OUT/'preflight.json').exists(),'Retain prior receipt'
    identity=typed_codec.frozen(ROOT/'contracts/typed_codec_v1.json')
    path=ROOT/'runs/typed-real-dev-v5/pairs.jsonl'
    assert sha(path)=='566d6b440d7fdd16bac0b86114b5e8dd35ba8bd646b6bd304f8cfbc5e201330e'
    pairs=typed_confirmation.verify_development(path,ROOT/'findings/typed-real-dev-v5/summary.json',identity)
    fit=[p for p in pairs if p['learning_split']=='development_fit']
    unique={}
    for p in fit:unique.setdefault(p['uid'],p)
    verify_weights();tokenizer=AutoTokenizer.from_pretrained(EMBEDDING_DIR,local_files_only=True)
    rows=[]
    for p in fit:
        program=p['target']['program'];compact=json.dumps(program,sort_keys=True,separators=(',',':'));assert json.loads(compact)==program
        old=typed_codec.digest(p['target'])+' '+json.dumps(program,sort_keys=True)
        new=typed_codec.digest(p['target'])+' '+compact
        rows.append(dict(kind='fit_graph',uid=p['uid'],target_sha256=typed_codec.digest(p['target']),original_tokens=len(tokenizer(old,truncation=False)['input_ids']),compact_tokens=len(tokenizer(new,truncation=False)['input_ids']),original_text_sha256=__import__('hashlib').sha256(old.encode()).hexdigest(),compact_text_sha256=__import__('hashlib').sha256(new.encode()).hexdigest()))
    for p in unique.values():
        text=INSTRUCTION+query_text(p)
        rows.append(dict(kind='query',uid=p['uid'],original_tokens=len(tokenizer(text,truncation=False)['input_ids']),compact_tokens=len(tokenizer(text,truncation=False)['input_ids']),text_sha256=__import__('hashlib').sha256(text.encode()).hexdigest()))
    maximum=max(r['compact_tokens'] for r in rows)
    result=dict(name=OUT.name,corpus_sha256=sha(path),codec_sha256=identity,driver_sha256=sha(Path(__file__)),fit_graphs=len(fit),fit_queries=len(unique),rows=rows,maximum_compact_tokens=maximum,compact_inputs_fit_existing1024=maximum<=1024,model_loaded=False,embeddings_computed=False,training_started=False,protected_opened=False,audit_queries_opened=False,tokenizer_config_maximum=tokenizer.model_max_length)
    publish(OUT/'preflight.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
