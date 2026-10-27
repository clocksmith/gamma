"""Native identity/cyclic-node adapter checks, independently constructed graphs."""
from pathlib import Path
from types import SimpleNamespace as Node
import importlib.util,subprocess,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def load(i):
 s=importlib.util.spec_from_file_location('x'+str(i),ROOT/'python'/f'{i}.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m.solve
f=load(2046);g=load(2773);count=0
for vals in [[0,2,-5,5,10,-10],[-1,-2,-3],[1,2,3],[0],[-1,1,-2,2]]:
 nodes=[Node(val=v,next=None) for v in vals]
 for a,b in zip(nodes,nodes[1:]):a.next=b
 h=f(nodes[0]);got=[];ids=[]
 while h:got.append(h.val);ids.append(id(h));h=h.next
 assert got==sorted(vals) and set(ids)==set(map(id,nodes)) and len(ids)==len(nodes);count+=1
for values in [[1],[1,2],[1,2,3],[1,2,3,None,None,4,5]]:
 nodes=[Node(val=values[0],left=None,right=None)];i=0;p=1;depth=[0]
 while p<len(values):
  for side in ('left','right'):
   if p<len(values) and values[p] is not None:
    node=Node(val=values[p],left=None,right=None);setattr(nodes[i],side,node);nodes.append(node);depth.append(depth[i]+1)
   p+=1
  i+=1
 leaves=sorted([v for v in nodes if v.left is None and v.right is None],key=lambda v:v.val)
 for i,v in enumerate(leaves):v.left=leaves[i-1];v.right=leaves[(i+1)%len(leaves)]
 assert g(nodes[0])==max(depth);count+=1
js=r'''const root=process.argv[1],f=require(root+'/javascript/2046.js'),g=require(root+'/javascript/2773.js');let count=0;for(const vals of [[0,2,-5,5,10,-10],[-1,-2,-3],[1,2,3],[0],[-1,1,-2,2]]){let ns=vals.map(val=>({val,next:null}));for(let i=1;i<ns.length;i++)ns[i-1].next=ns[i];let h=f(ns[0]),got=[],seen=new Set();while(h){got.push(h.val);seen.add(h);h=h.next;}if(JSON.stringify(got)!==JSON.stringify(vals.slice().sort((a,b)=>a-b))||seen.size!==ns.length||ns.some(v=>!seen.has(v)))throw Error('identity');count++;}for(const values of [[1],[1,2],[1,2,3],[1,2,3,null,null,4,5]]){let ns=[{val:values[0],left:null,right:null}],depth=[0],p=1;for(let i=0;p<values.length;i++)for(const side of ['left','right']){if(p<values.length&&values[p]!==null){let node={val:values[p],left:null,right:null};ns[i][side]=node;ns.push(node);depth.push(depth[i]+1);}p++;}let leaves=ns.filter(v=>!v.left&&!v.right).sort((a,b)=>a.val-b.val);for(let i=0;i<leaves.length;i++){leaves[i].left=leaves[(i+leaves.length-1)%leaves.length];leaves[i].right=leaves[(i+1)%leaves.length];}if(g(ns[0])!==Math.max(...depth))throw Error('cyclic height');count++;}console.log(JSON.stringify({passed:count}));'''
r=subprocess.run(['node','-e',js,str(ROOT)],capture_output=True,text=True,timeout=20);assert r.returncode==0,r.stderr
report={'python_passed':count,'javascript':json.loads(r.stdout),'ids':[2046,2773],'scope':'Authored native object fixtures only; node identity and circular leaf-link handling.'};(HERE/'native-test-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
