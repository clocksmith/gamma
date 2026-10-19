from pathlib import Path
from collections import defaultdict,Counter
import json,hashlib,sys
T=Path('/home/x/Documents/Codex/2026-10-19/task');sys.path.insert(0,str(T));import macro_codec as codec
O=Path('/home/x/deco/gamma/projects/algorithm_solver/runs/corpus-macro-analysis-128-v1');contract=json.loads((O/'contract.json').read_text());mined=json.loads((O/'mined-candidates.json').read_text());bylang={lang:[r for r in contract['source_rows'] if r['language']==lang] for lang in ['javascript','python']}
results=[];fragment_records=[]
for lang,rows in bylang.items():
 texts=[Path(r['source']).read_text() for r in rows];selected=[]
 bfs=next(g for g in mined if g['language']==lang and g['kind']==('ForOfStatement' if lang=='javascript' else 'For') and set(g['ids'])=={102,103,107})
 dup=[g for g in mined if g['language']==lang and g['kind']==('WhileStatement' if lang=='javascript' else 'While') and set(g['ids'])=={15,18}]
 assert len(dup)==2
 fragments=[dict(name='bfs_collect_one_level',variants=[],precondition='Acyclic binary tree nodes; level output empty. JS source frontier is not modified during iteration; next-frontier is separate. Python deque initial length defines level size; appending children is intentional.',effects='JS appends values and children to two distinct output arrays. Python consumes current nodes and appends children on the same deque; appends values to a separate list. Bound temporaries must be fresh, distinct from operand handles.',fixed_constants='Tree field names val,left,right; traversal order left before right; Python len(q) evaluated once.'),dict(name='skip_adjacent_equal_values',variants=[],precondition='Integer in-range pointers into sorted dense numeric array, after emitting a tuple and moving both pointers. Compare only while left<right.',effects='Moves one pointer inward over values equal to the just-emitted neighbor; reads array without mutation. Language equality retains original semantics.',fixed_constants='Offset and step of one; direction is a charged variant byte, not a free channel.')]
 occurrences=defaultdict(list)
 for fi,groups in enumerate([[bfs],dup]):
  for variant,g in enumerate(groups):
   exemplar=g['occurrence_records'][0];tmpl,_=codec.template(exemplar['text'],exemplar['identifiers']);fragments[fi]['variants'].append(tmpl)
   for occ in g['occurrence_records']:
    actual,indent=codec.template(occ['text'],occ['identifiers']);assert actual==tmpl,(lang,fi,occ['id'])
    assert codec.expand(tmpl,occ['identifiers'],list(range(len(occ['identifiers']))),indent)==occ['text'].encode()
    row=next(r for r in rows if r['id']==occ['id']);src=Path(row['source']).read_text();start=occ.get('start')
    if start is None:start=src.index(occ['text'],sum(len(s) for s in src.splitlines(keepends=True)[:occ['line']-1]))
    assert src[start:start+len(occ['text'])]==occ['text'];byte_start=len(src[:start].encode())
    occurrences[occ['id']].append(dict(start=byte_start,text=occ['text'],names=occ['identifiers'],indent=indent,code=254+fi,variant=variant,shape_sha256=g['shape_sha256']))
  fragment_records.append(dict(language=lang,name=fragments[fi]['name'],ids=sorted({r['id'] for g in groups for r in g['occurrence_records']}),occurrences=sum(len(g['occurrence_records']) for g in groups),raw_fragment_bytes=sum(g['raw_bytes'] for g in groups),variants=len(groups),contracts={k:v for k,v in fragments[fi].items() if k!='variants'},round_trips_passed=True))
 books={kind:codec.book(lang,kind,texts,fragments) for kind in ['lexical','semantic','whole']}
 out=O/lang;out.mkdir()
 for kind,b in books.items():
  (out/f'{kind}-codebook.json').write_bytes(codec.canonical(b));d=out/kind;d.mkdir();individual=[]
  for i,(row,src) in enumerate(zip(rows,texts)):
   stream,stats=codec.encode(src,b,occurrences[row['id']] if kind=='semantic' else (),whole_index=i)
   decoded=codec.decode(stream,b);assert decoded==src.encode();again,_=codec.encode(decoded.decode(),b,occurrences[row['id']] if kind=='semantic' else (),whole_index=i);assert again==stream
   (d/f"{row['id']:04d}.bin").write_bytes(stream)
   if kind=='semantic':(d/f"{row['id']:04d}.{'js' if lang=='javascript' else 'py'}").write_bytes(decoded)
   individual.append(dict(id=row['id'],source_bytes=len(src.encode()),encoded_bytes=len(stream),bits=len(stream)*8,stream_sha256=hashlib.sha256(stream).hexdigest(),source_sha256=row['source_sha256'],**stats))
  total=sum(r['encoded_bytes'] for r in individual);booksize=len(codec.canonical(b));records=dict(language=lang,profile=kind,slots=len(b['entries']),codebook_bytes=booksize,total_stream_bytes=total,total_stream_bits=8*total,one_corpus_pass_including_codebook_bytes=total+booksize,source_bytes=sum(r['source_bytes'] for r in individual),framing_binding_bytes=sum(r['header_binding_bytes'] for r in individual),body_bytes=sum(r['body_bytes'] for r in individual),end_control_bytes=len(individual),source_exact_roundtrips=len(individual),canonical_stream_roundtrips=len(individual),fragment_calls=sum(r['fragment_uses'] for r in individual),fragment_problem_ids=[r['id'] for r in individual if r['fragment_uses']],whole_calls=sum(r['whole_uses'] for r in individual),fallback_scope='Literal/lexical remainder is explicitly counted; partial fragment reuse is not macro-only full-program coverage.',rows=individual)
  (out/f'{kind}-summary.json').write_text(json.dumps(records,indent=2)+'\n');results.append(records)
 (out/'fragment-occurrences.json').write_text(json.dumps(dict(occurrences),indent=2)+'\n')
summary=dict(source_contract_sha256=hashlib.sha256((O/'contract.json').read_bytes()).hexdigest(),codec_sha256=hashlib.sha256((T/'macro_codec.py').read_bytes()).hexdigest(),analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),profiles=results,fragments=fragment_records,method='Fixed8-bit corpus-fitted lexical IDs versus124 lexical shortcuts plus two reviewed parameterized fragments versus94 exact whole-solution entries. Source-aware segmentation is an offline representation oracle; no autonomous selection model. Bindings and operands are paid in each stream; all dictionary bytes are paid separately.',limitations='In-sample, error-free encoding study. Not trained/predicted output, generalization, human speed, shortest possible vocabulary, or complete semantic coverage. All94 files use literal/lexical remainder with the two-fragment profile; whole-solution baseline embeds all94 bodies in its bounded dictionary.',protected_opened=False,training=False)
(O/'analysis-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='rows'} for r in results],indent=2));print(json.dumps(fragment_records,indent=2))
