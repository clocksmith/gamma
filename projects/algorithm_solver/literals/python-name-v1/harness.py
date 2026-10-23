"""Candidate execution only: input transport and observations, no expected values."""
import copy,importlib.util,json,math

def value(x):
 if x is None or type(x) in (str,bool,int):return x
 if type(x) is float:
  if not math.isfinite(x):return {'$float':repr(x)}
  return x
 if type(x) in (list,tuple):return [value(y) for y in x]
 if type(x) is dict:return {str(k):value(v) for k,v in x.items()}
 if type(x) in (set,frozenset):return {'$set':sorted([value(y) for y in x],key=repr)}
 raise TypeError('unsupported result type '+type(x).__name__)
def graph(args,result):
 seen={};edges=[]
 def visit(x,path):
  if type(x) not in (list,dict,tuple,set):return
  ident=id(x)
  if ident in seen:edges.append([path,seen[ident]]);return
  seen[ident]=path
  if type(x) in (list,tuple):
   for i,y in enumerate(x):visit(y,path+'/'+str(i))
  elif type(x) is dict:
   for k,y in x.items():visit(y,path+'/'+str(k))
 for i,x in enumerate(args):visit(x,'arg/'+str(i))
 visit(result,'result');return edges

def run(source,entry,calls):
 spec=importlib.util.spec_from_file_location('candidate',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 for i,call in enumerate(calls):
  args=copy.deepcopy(call['args']);before=value(args);result=None;error=None
  try:result=getattr(module.Solution(),entry)(*args)
  except Exception as e:error={'type':type(e).__name__,'message':str(e)}
  rec={'i':i,'result':value(result),'result_type':type(result).__name__,'args_before':before,'args_after':value(args),'aliases':graph(args,result),'error':error}
  print(json.dumps(rec,ensure_ascii=True,allow_nan=False),flush=True)
 print(json.dumps({'done':len(calls)}),flush=True)
if __name__=='__main__':
 data=json.load(open('inputs.json'));run('candidate.py',data['entry'],data['calls'])
