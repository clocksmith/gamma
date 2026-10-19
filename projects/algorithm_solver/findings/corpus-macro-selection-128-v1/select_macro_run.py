from pathlib import Path
from collections import Counter
import hashlib,itertools,json,sys,time
T=Path('/home/x/Documents/Codex/2026-10-19/task');sys.path.insert(0,str(T));import selection_codec as c
R=Path('/home/x/deco/gamma/projects/algorithm_solver');P=R/'runs/corpus-macro-analysis-128-v1';O=R/'runs/corpus-macro-selection-128-v1';contract=json.loads((O/'contract.json').read_text());menu=json.loads((O/'candidate-menu.json').read_text());results=[]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
print('[run-contract] run_name=bounded-macro-selection pairs_input_spec=frozen94pairs resume_from=none resume_stage=none decode=source-aware-optimal-registered-occurrences eval_dataset_paths=32JS+16Python-subsets device=cpu schedule=serial runtime_mode=cpu sweep_mode=none',flush=True)
for lang in ['javascript','python']:
 rows=[r for r in contract['source_rows'] if r['language']==lang];texts=[Path(r['source']).read_text() for r in rows];candidates=[m for m in menu if m['language']==lang];fragments=[];occurrences=[]
 for m in candidates:
  variants=[];occ=[]
  for variant,g in enumerate(m['groups']):
   ex=g['occurrence_records'][0];names=[n for n in ex['identifiers'] if n not in m['fixed_global_names']];tmpl,_=c.template(ex['text'],names);variants.append(tmpl)
   for a in g['occurrence_records']:
    names=[n for n in a['identifiers'] if n not in m['fixed_global_names']];actual,indent=c.template(a['text'],names);assert actual==tmpl,(lang,m['name'],a['id']);assert c.expand(tmpl,names,list(range(len(names))),indent)==a['text'].encode()
    src=next(t for r,t in zip(rows,texts) if r['id']==a['id']);start=a.get('start')
    if start is None:start=src.index(a['text'],sum(len(s) for s in src.splitlines(keepends=True)[:a['line']-1]))
    assert src[start:start+len(a['text'])]==a['text'];occ.append(dict(id=a['id'],name=m['name'],start=len(src[:start].encode()),text=a['text'],names=names,indent=indent,variant=variant))
  fragments.append({**m['contract'],'name':m['name'],'variants':variants});occurrences.append(occ)
 dest=O/lang;dest.mkdir();(dest/'candidate-fragments.json').write_text(json.dumps(fragments,indent=2)+'\n');subset_results=[];starttime=time.monotonic()
 for mask in range(1<<len(candidates)):
  chosen=[i for i in range(len(candidates)) if mask>>i&1];fs=[fragments[i] for i in chosen];b=c.book(lang,'semantic',texts,fs);d=dest/f'subset-{mask:02d}';d.mkdir();(d/'codebook.json').write_bytes(c.canonical(b));byid={r['id']:[] for r in rows}
  for index,i in enumerate(chosen):
   for o in occurrences[i]:byid[o['id']].append({**o,'code':256-len(chosen)+index})
  measurements=[]
  for row,source in zip(rows,texts):
   stream,stats=c.encode(source,b,byid[row['id']]);assert c.decode(stream,b)==source.encode();(d/f"{row['id']:04d}.bin").write_bytes(stream)
   measurements.append(dict(id=row['id'],key=row['key'],source_bytes=len(source.encode()),encoded_bytes=len(stream),stream_sha256=hashlib.sha256(stream).hexdigest(),**stats))
  rec=dict(mask=mask,selected=[candidates[i]['name'] for i in chosen],macro_count=len(chosen),slots=len(b['entries']),input_bytes=sum(r['encoded_bytes'] for r in measurements),codebook_bytes=len(c.canonical(b)),source_bytes=sum(r['source_bytes'] for r in measurements),fragment_calls=sum(r['fragment_uses'] for r in measurements),fragment_problem_ids=[r['id'] for r in measurements if r['fragment_uses']],lexical_remainder_source_bytes=sum(r['lexical_remainder_source_bytes'] for r in measurements),fragment_source_bytes=sum(r['fragment_source_bytes'] for r in measurements),reconstruction_passes=len(rows),rows=measurements)
  (d/'summary.json').write_text(json.dumps(rec,indent=2)+'\n');subset_results.append(rec)
 best=min(subset_results,key=lambda r:(r['input_bytes'],r['macro_count'],r['mask']));attribution=[]
 for i,m in enumerate(candidates):
  on=bool(best['mask']>>i&1);without=subset_results[best['mask']&~(1<<i)];withone=subset_results[best['mask']|(1<<i)];uses=[u for r in best['rows'] for u in r['used'] if u['name']==m['name']]
  attribution.append(dict(name=m['name'],selected=on,selected_calls=len(uses),selected_problem_ids=sorted({r['id'] for r in best['rows'] if any(u['name']==m['name'] for u in r['used'])}),available_occurrences=len(occurrences[i]),available_problem_ids=sorted({r['id'] for r in occurrences[i]}),leave_one_out_input_penalty=without['input_bytes']-best['input_bytes'] if on else None,add_one_input_change=withone['input_bytes']-best['input_bytes'] if not on else None,singleton_input_saving=subset_results[0]['input_bytes']-subset_results[1<<i]['input_bytes'],selected_instruction_bytes=sum(u['instruction_bytes'] for u in uses),selected_source_bytes=sum(u['source_bytes'] for u in uses),identifier_arities=[v['arity'] for v in fragments[i]['variants']],variants=len(fragments[i]['variants']),interpretability=fragments[i]['interpretability']))
 old={kind:json.loads((P/lang/f'{kind}-summary.json').read_text()) for kind in ['lexical','semantic','whole']};assert subset_results[0]['input_bytes']==old['lexical']['total_stream_bytes']
 report=dict(language=lang,best_mask=best['mask'],best={k:v for k,v in best.items() if k!='rows'},subsets=[{k:v for k,v in r.items() if k!='rows'} for r in subset_results],attribution=attribution,baseline_input_bytes={k:v['total_stream_bytes'] for k,v in old.items()},incremental_saving_over_two_fragment=old['semantic']['total_stream_bytes']-best['input_bytes'],saving_over_lexical=old['lexical']['total_stream_bytes']-best['input_bytes'],wall_seconds=time.monotonic()-starttime,analysis_roundtrips=len(subset_results)*len(rows))
 (dest/'selection.json').write_text(json.dumps(report,indent=2)+'\n');results.append(report);print(lang,'best',best['selected'],'input',best['input_bytes'],'saving vs lexical',report['saving_over_lexical'],'increment over prior',report['incremental_saving_over_two_fragment'],flush=True)
summary=dict(contract_sha256=sha(O/'contract.json'),codec_sha256=sha(T/'selection_codec.py'),runner_sha256=sha(__file__),languages=results,selection_is_algorithmic=True,candidate_menu_is_hand_reviewed=True,objective='Complete input bytes, not dictionary storage.',autonomous_solves=0)
(O/'selection-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
