from pathlib import Path
from collections import defaultdict
import ast,json,hashlib,subprocess
T=Path('/home/x/Documents/Codex/2026-10-19/task');O=Path('/home/x/deco/gamma/projects/algorithm_solver/runs/corpus-macro-analysis-128-v1');contract=json.loads((O/'contract.json').read_text());rows=contract['source_rows']
js=json.loads(subprocess.check_output(['node',str(T/'macro_ast_scan.cjs')],input=json.dumps([r for r in rows if r['language']=='javascript']),text=True));records=js
fixed=set(['len','range','enumerate','min','max','abs','sum','sorted','list','dict','set','zip','int','str','bool','float','Counter','defaultdict','bisect_left','bisect_right','ListNode','TreeNode','inf'])
for row in rows:
 if row['language']!='python':continue
 source=Path(row['source']).read_text();tree=ast.parse(source);lines=source.splitlines(keepends=True);offset=[0]
 for line in lines:offset.append(offset[-1]+len(line.encode()))
 for n in ast.walk(tree):
  if not isinstance(n,ast.stmt) or isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.Assign,ast.AnnAssign)):continue
  text=ast.get_source_segment(source,n)
  if not text or not 20<=len(text)<=700 or len(list(ast.walk(n)))<5:continue
  names={}
  def norm(v):
   if isinstance(v,list):return [norm(x) for x in v]
   if not isinstance(v,ast.AST):return v
   if isinstance(v,ast.Name):
    name=v.id
    if name not in fixed:
     if name not in names:names[name]='v'+str(len(names))
     name=names[name]
    return {'type':'Name','id':name,'ctx':type(v.ctx).__name__}
   return {'type':type(v).__name__,**{k:norm(x) for k,x in ast.iter_fields(v)}}
  shape=norm(n);records.append(dict(id=row['id'],language='python',kind=type(n).__name__,text=text,shape=shape,nodes=len(list(ast.walk(n))),identifiers=list(names),line=n.lineno))
groups=defaultdict(list)
for r in records:
 h=hashlib.sha256(json.dumps(r['shape'],sort_keys=True).encode()).hexdigest();groups[r['language'],h].append(r)
ranked=[]
for (lang,h),occ in groups.items():
 ids=sorted({r['id'] for r in occ})
 if len(ids)<2:continue
 ranked.append(dict(language=lang,shape_sha256=h,kind=occ[0]['kind'],distinct_problems=len(ids),ids=ids,occurrences=len(occ),raw_bytes=sum(len(r['text'].encode()) for r in occ),representative=occ[0]['text'],occurrence_records=occ,semantic_status='Syntactic candidate only; no substitution or semantics approval from structural matching.'))
ranked.sort(key=lambda r:(-r['raw_bytes'],-r['distinct_problems'],r['shape_sha256']))
(O/'mined-candidates.json').write_text(json.dumps(ranked,indent=2)+'\n')
for lang in ['javascript','python']:
 print(lang,'recurring groups',sum(r['language']==lang for r in ranked))
 for r in [r for r in ranked if r['language']==lang][:8]:print(r['kind'],r['ids'],r['occurrences'],r['raw_bytes'],repr(r['representative'][:170]))
