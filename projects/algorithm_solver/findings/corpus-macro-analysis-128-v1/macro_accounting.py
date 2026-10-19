from pathlib import Path
from collections import Counter
import hashlib,json,sys,math
T=Path('/home/x/Documents/Codex/2026-10-19/task');sys.path.insert(0,str(T));import macro_codec as c
O=Path('/home/x/deco/gamma/projects/algorithm_solver/runs/corpus-macro-analysis-128-v1');summary=json.loads((O/'analysis-summary.json').read_text());records=[]
def inspect(data,b):
 counts=Counter(header_bytes=38);n,p=c.readvar(data,38);counts['binding_count_bytes']=p-38
 for _ in range(n):
  start=p;length,p=c.readvar(data,p);counts['binding_length_bytes']+=p-start;counts['binding_identifier_bytes']+=length;p+=length
 table={e['id']:e for e in b['entries']}
 while p<len(data):
  code=data[p];p+=1;e=table[code];k=e['kind']
  if k=='end':counts['end_bytes']+=1
  elif k=='whole':counts['whole_macro_id_bytes']+=1
  elif k=='text':counts['ascii_id_bytes' if code<130 else 'lexical_shortcut_id_bytes']+=1
  elif k=='literal_run':
   counts['literal_control_bytes']+=1;start=p;length,p=c.readvar(data,p);counts['literal_length_bytes']+=p-start;counts['literal_payload_bytes']+=length;p+=length
  else:
   counts['fragment_macro_id_bytes']+=1;v=data[p];p+=1;counts['variant_operand_bytes']+=1;start=p;_,p=c.readvar(data,p);counts['indent_operand_bytes']+=p-start
   for _ in range(e['variants'][v]['arity']):start=p;_,p=c.readvar(data,p);counts['binding_reference_operand_bytes']+=p-start
 assert sum(counts.values())==len(data);return counts
for profile in summary['profiles']:
 lang,kind=profile['language'],profile['profile'];b=json.loads((O/lang/f'{kind}-codebook.json').read_text());totals=Counter();rows=[]
 for row in profile['rows']:
  data=(O/lang/kind/f"{row['id']:04d}.bin").read_bytes();count=inspect(data,b);totals.update(count);rows.append(dict(id=row['id'],total_bytes=len(data),counts=dict(count)))
 assert sum(totals.values())==profile['total_stream_bytes'];records.append(dict(language=lang,profile=kind,totals=dict(totals),rows=rows))
comparisons=[]
for lang in ['javascript','python']:
 by={p['profile']:p for p in summary['profiles'] if p['language']==lang};base=by['lexical'];base_rows={r['id']:r for r in base['rows']}
 for kind in ['semantic','whole']:
  x=by[kind];saving=base['total_stream_bytes']-x['total_stream_bytes'];extra=x['codebook_bytes']-base['codebook_bytes'];comparisons.append(dict(language=lang,profile=kind,stream_bytes_saved=saving,codebook_extra_bytes=extra,one_corpus_pass_bytes_saved=saving-extra,repetitions_for_strict_total_saving=math.floor(extra/saving)+1 if saving>0 else None))
 for fragment,ids in [('bfs_collect_one_level',[102,103,107]),('skip_adjacent_equal_values',[15,18])]:
  target={r['id']:r for r in by['semantic']['rows']};comparisons.append(dict(language=lang,fragment=fragment,ids=ids,lexical_complete_bytes=sum(base_rows[n]['encoded_bytes'] for n in ids),hybrid_complete_bytes=sum(target[n]['encoded_bytes'] for n in ids),complete_stream_saving=sum(base_rows[n]['encoded_bytes']-target[n]['encoded_bytes'] for n in ids),caveat='Includes actual program framing, identifier table and nonfragment remainder. Same language profile also replaces two lexical slots; not independent additive causal attribution.'))
report=dict(profiles=records,comparisons=comparisons,shared_codec_implementation_bytes=(T/'macro_codec.py').stat().st_size,codebook_cost='Exact canonical UTF8 JSON bytes, including bodies, schema, semantic contracts and constants. Common codec implementation reported separately, not charged once per program.',fixed_constants='Offset/step1, val/left/right fields, equality and traversal controls reside in charged template bodies. All selectable direction, indentation and binding references are in stream bytes.',human_input='Every stream byte is8 ideal binary presses. No corrections/navigation are encoded in these error-free source-aware streams. No measured human timing or autonomous choice claim.')
(O/'accounting.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(comparisons,indent=2))
