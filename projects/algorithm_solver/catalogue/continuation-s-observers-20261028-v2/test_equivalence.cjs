"use strict";
// v1/v2 observer equivalence on seeded synthetic inputs. Source-free: every
// program here is a hand-written synthetic function/class; no numbered
// candidate file is read or executed. For each case both observers get a
// fresh, identically seeded synthetic namespace. The test requires equal
//   (a) record JSON or error string, as main() would print it, and
//   (b) logs of candidate-observable events: Proxy traps, toJSON calls and
//       constructor calls, in order.
// Usage: node test_equivalence.cjs [cases-per-route] [seed]
const path=require('path'),assert=require('assert');
const LANE=path.basename(__dirname).includes('-t-observers-')?'t':'s';
const V1=path.join(__dirname,'..',`continuation-${LANE}-observers-20261028-v1`);
const v1=require(path.join(V1,'harness.cjs')),v2=require('./harness.cjs');
const CASES=Number(process.argv[2]||400),SEED=Number(process.argv[3]||20261028);

function rng(seed){let s=seed>>>0||1;return()=>{s^=s<<13;s>>>=0;s^=s>>>17;s^=s<<5;s>>>=0;return s/4294967296;};}
const int=(r,lo,hi)=>lo+Math.floor(r()*(hi-lo+1));
const pick=(r,a)=>a[Math.floor(r()*a.length)];
function shuffle(r,a){for(let i=a.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}

// ---- routes ----
const T={226:{kind:'tree',fn:'invertTree',lim:100,lo:-100,hi:100,min:0,uniq:false,bst:false,req:false},
 230:{kind:'tree',fn:'kthSmallest',lim:10000,lo:0,hi:10000,min:1,uniq:true,bst:true,req:false},
 234:{kind:'list',fn:'isPalindrome',lim:100000,lo:0,hi:9,min:1,uniq:false,req:false},
 235:{kind:'tree',fn:'lowestCommonAncestor',lim:100000,lo:-1e9,hi:1e9,min:2,uniq:true,bst:true,req:true},
 236:{kind:'tree',fn:'lowestCommonAncestor',lim:100000,lo:-1e9,hi:1e9,min:2,uniq:true,bst:false,req:true},
 237:{kind:'list',fn:'deleteNode',lim:1000,lo:-1000,hi:1000,min:2,uniq:true,req:true}};
const S={199:{kind:'tree',fn:'rightSideView',lim:100,lo:-100,hi:100,min:0},
 203:{kind:'list',fn:'removeElements',lim:10000,lo:1,hi:50,min:0},
 206:{kind:'list',fn:'reverseList',lim:5000,lo:-5000,hi:5000,min:0},
 222:{kind:'tree',fn:'countNodes',lim:50000,lo:0,hi:50000,min:0,complete:true}};
const ROUTES=LANE==='t'?T:S;

// ---- wires (mostly valid, some invalid on purpose) ----
function values(r,spec,n){
  if(spec.uniq||spec.bst){const set=new Set();while(set.size<n)set.add(int(r,spec.lo,spec.hi));const a=[...set];return spec.bst?a.sort((x,y)=>x-y):a;}
  return Array.from({length:n},()=>int(r,spec.lo,spec.hi));
}
function treeWire(r,spec,n){
  const vals=values(r,spec,n),left=Array(n).fill(null),right=Array(n).fill(null);
  if(n===0)return {values:vals,left,right,root:null};
  if(spec.complete){for(let i=0;i<n;i++){if(2*i+1<n)left[i]=2*i+1;if(2*i+2<n)right[i]=2*i+2;}return {values:vals,left,right,root:0};}
  if(spec.bst){ // random BST shape over sorted vals, root picked by recursion
    let root=null;const stack=[[0,n-1,null,null]];
    while(stack.length){const [lo,hi,parent,side]=stack.pop();if(lo>hi)continue;const mid=int(r,lo,hi);if(parent===null)root=mid;else(side==='l'?left:right)[parent]=mid;stack.push([lo,mid-1,mid,'l'],[mid+1,hi,mid,'r']);}
    return {values:vals,left,right,root};
  }
  const order=shuffle(r,Array.from({length:n},(_,i)=>i)),slots=[[order[0],'l'],[order[0],'r']];
  for(let k=1;k<n;k++){const s=slots.splice(int(r,0,slots.length-1),1)[0];(s[1]==='l'?left:right)[s[0]]=order[k];slots.push([order[k],'l'],[order[k],'r']);}
  return {values:vals,left,right,root:order[0]};
}
function listWire(r,spec,n){
  const vals=values(r,spec,n),order=shuffle(r,Array.from({length:n},(_,i)=>i)),next=Array(n).fill(null);
  if(LANE==='t'&&spec.fn==='isPalindrome'&&r()<0.5)for(let i=0;i<n;i++)vals[order[n-1-i]]=vals[order[i]];
  for(let k=0;k+1<n;k++)next[order[k]]=order[k+1];return {values:vals,next,head:n?order[0]:null};
}
function corrupt(r,wire,kind){
  const w=JSON.parse(JSON.stringify(wire)),n=w.values.length,e=kind==='tree'?pick(r,['left','right']):'next';
  switch(int(r,0,8)){
   case 0:if(n)w[e][int(r,0,n-1)]=int(r,0,n-1);break;          // cycle/alias
   case 1:if(n)w[e][int(r,0,n-1)]=n+3;break;                    // out of range
   case 2:if(n)w.values[int(r,0,n-1)]=1.5;break;                // non-integer
   case 3:w.extra=1;break;                                      // extra key
   case 4:if(n>1){const i=int(r,0,n-1);w.values[i]=w.values[(i+1)%n];}break; // duplicate
   case 5:w[kind==='tree'?'root':'head']=n?int(r,0,n-1):0;break;
   case 6:if(n)w.values[int(r,0,n-1)]=1e12;break;               // out of domain
   case 7:w[e]=w[e].slice(0,Math.max(0,n-1));break;
   case 8:w.values=w.values.concat(Array(5).fill(1));break;
  }
  return w;
}

// ---- synthetic namespace: node class + official function, with event log ----
function namespace(pid,spec,seed,log){
  const r=rng(seed),fields=spec.kind==='tree'?['left','right']:['next'],ctorMode=r()<0.4?int(r,0,1):r()<0.3?int(r,19,23):int(r,0,18),k=int(r,0,6);let built=0,poisonKey=null,saved=null,armed=false,armedCount=0,armedRoot=null;
  const trap=(tag,target)=>new Proxy(target,{getPrototypeOf(t){log.push(tag+':gp');return Reflect.getPrototypeOf(t);},ownKeys(t){log.push(tag+':ok');return Reflect.ownKeys(t);},getOwnPropertyDescriptor(t,p){log.push(tag+':gopd:'+String(p));return Reflect.getOwnPropertyDescriptor(t,p);},get(t,p,rcv){log.push(tag+':get:'+String(p));return Reflect.get(t,p,rcv);},set(t,p,v,rcv){log.push(tag+':set:'+String(p));return Reflect.set(t,p,v,rcv);}});
  const nodes=[];
  function init(self,val,a,b){
   if(spec.req){self.val=val;for(const f of fields)self[f]=null;}
   else{self.val=val===undefined?0:val;self[fields[0]]=a===undefined?null:a;if(fields[1])self[fields[1]]=b===undefined?null:b;}
  }
  function hook(self){const out=hookInner(self);nodes.push(out);return out;}
  function hookInner(self){
   built++;log.push('ctor:'+built);const at=built===k+2;
   switch(ctorMode){
    case 2:return trap('pn'+built,self);                                         // every node a Proxy
    case 3:return at?trap('pk',self):self;                                        // one Proxy node
    case 4:if(at){poisonKey='__eq_transient';Object.prototype.__eq_transient=1;}else if(built===k+3&&poisonKey){delete Object.prototype.__eq_transient;}return self; // transient
    case 5:if(at&&nodes.length)nodes[0].val='x';return self;                      // mutate earlier node
    case 6:if(at&&nodes.length)return nodes[nodes.length-1];return self;          // duplicate identity
    case 8:if(at)throw Error('ctor failure');return self;
    case 9:if(at){let v=self.val;Object.defineProperty(self,'val',{get(){return v;},set(x){v=x;},enumerable:true,configurable:true});}return self;
    case 10:if(at)Node.prototype.extra=function(){};return self;                 // persistent prototype change
    case 11:if(at)Function.prototype.__eq_fp=1;else if(built===k+3)delete Function.prototype.__eq_fp;return self;
    case 12:if(at&&nodes.length)nodes[0][fields[0]]=trap('edge',{});return self;
    case 13:if(at)Object.defineProperty(self,fields[0],{value:null,writable:false,enumerable:true,configurable:true});return self;
    case 14:if(at)Object.defineProperty(self,'val',{value:self.val,writable:true,enumerable:false,configurable:true});return self;
    case 15:if(at)Object.prototype.__eq_persist=1;return self;
    case 16:if(at)Object.defineProperty(Object.prototype,'toString',{enumerable:true});else if(built===k+3)Object.defineProperty(Object.prototype,'toString',{enumerable:false});return self; // transient attribute
    case 17:if(at){saved=Object.prototype.valueOf;Object.prototype.valueOf=function(){return 0;};}else if(built===k+3&&saved)Object.prototype.valueOf=saved;return self; // transient value, same keys
    case 18:if(at)Object.defineProperty(Function.prototype,'apply',{writable:false});else if(built===k+3)Object.defineProperty(Function.prototype,'apply',{writable:true});return self;
   }
   return self;
  }
  let Node;
  if(ctorMode===1){Node=class{constructor(val,a,b){init(this,val,a,b);const o=hook(this);if(o!==this)return o;}};}
  else if(ctorMode===7){Node=function(val){this.val=val;for(const f of fields)this[f]=undefined;};}
  else{Node=function(val,a,b){init(this,val,a,b);const o=hook(this);if(o!==this)return o;};}
  // Modes 19-23: a Proxy on the class chain. Every trap is logged; modes 21-23
  // arm during the official call and throw once, keep throwing, or mutate a node.
  if(ctorMode>=19){
   const onPrototype=ctorMode===20||ctorMode===23,at=k+1;
   const handler={getPrototypeOf(t){log.push('chain:gp');if(armed){armedCount++;
     if(ctorMode===21&&armedCount===at)throw Error('chain-trap-once-'+armedCount);
     if(ctorMode===22&&armedCount>=at)throw Error('chain-trap-reject-'+armedCount);
     if(ctorMode===23&&armedCount===at&&armedRoot)armedRoot.val=9;}
     return Reflect.getPrototypeOf(t);},
    ownKeys(t){log.push('chain:ok');return Reflect.ownKeys(t);},
    getOwnPropertyDescriptor(t,q){log.push('chain:gopd:'+String(q));return Reflect.getOwnPropertyDescriptor(t,q);}};
   if(onPrototype)Object.setPrototypeOf(Node.prototype,new Proxy(Object.prototype,handler));
   else Object.setPrototypeOf(Node,new Proxy(Function.prototype,handler));
  }
  const ns={};
  const ctorName=spec.kind==='tree'?'TreeNode':'ListNode';
  Object.defineProperty(Node,'name',{value:ctorName});
  ns[ctorName]=Node;
  const behaviour=r()<0.45?pick(r,[0,1,2,6,25,26,27]):int(r,0,33); // about half benign
  const all=root=>{const out=[],seen=new Set(),todo=root?[root]:[];while(todo.length){const x=todo.pop();if(x===null||typeof x!=='object'||seen.has(x))continue;seen.add(x);out.push(x);for(const f of fields)todo.push(x[f]);}return out;};
  ns[spec.fn]=function(...args){
   log.push('call:'+args.length);armed=true;armedCount=0;armedRoot=args[0]&&typeof args[0]==='object'?args[0]:null;
   const root=args[0],pool=all(root),any=()=>pool.length?pick(r,pool):null,f=pick(r,fields);
   switch(behaviour){
    case 0:return LANE==='t'&&[235,236].includes(pid)?args[1]:root;
    case 1:if(LANE==='t'&&[235,236].includes(pid))return args[2];return root;
    case 2:for(const x of pool)if(spec.kind==='tree'){const t=x.left;x.left=x.right;x.right=t;}return root;
    case 3:return new Node(5);
    case 4:return null;
    case 5:return undefined;
    case 6:return 7;
    case 7:return {toJSON(){log.push('toJSON');const x=any();if(x)x.val=3;return 1;}};
    case 8:{const x=any();if(x)x[f]=new Node(4);return root;}
    case 9:{const x=any();if(x&&pool.length)x[f]=trap('child',pool[0]);return root;}
    case 10:{const x=any();if(x)x[f]=root;return root;}
    case 11:{const x=any(),y=any();if(x&&y)x[f]=y[f]??y;return root;}
    case 12:{const x=any();if(x)x.val=pick(r,[1.5,'3',2**60,-0,null]);return root;}
    case 13:{const x=any();if(x)Object.defineProperty(x,'val',{writable:false});return root;}
    case 14:{const x=any();if(x)Object.defineProperty(x,'val',{enumerable:false});return root;}
    case 15:{const x=any();if(x)x.extra=1;return root;}
    case 16:{const x=any();if(x)delete x[f];return root;}
    case 17:{const x=any();if(x){let v=x.val;Object.defineProperty(x,'val',{get(){return v;},configurable:true,enumerable:true});}return root;}
    case 18:{const x=any();if(x)Object.setPrototypeOf(x,{});return root;}
    case 19:Node.prototype.added=1;return root;
    case 20:Object.prototype.__eq_call=1;delete Object.prototype.__eq_call;return root; // restored inside call: legal in both
    case 21:Object.prototype.__eq_call2=1;return root;                                   // not restored
    case 22:ns[spec.fn]=function(){};return root;
    case 23:{const x=any();if(x)Object.freeze(x);return root;}
    case 24:return root?trap('result',root):root;
    case 25:return any();
    case 26:{if(spec.kind==='list'&&root&&root.next){const second=root.next;root.val=second.val;root.next=second.next;}return LANE==='t'&&pid===237?undefined:root;}
    case 27:{if(spec.kind==='list'){let prev=null,cur=root;while(cur){const n=cur.next;cur.next=prev;prev=cur;cur=n;}return prev;}return root;}
    case 28:return pick(r,[true,false,0,1,10n,'s',Symbol.iterator]);
    case 29:{const x=any();if(x)x[f]=trap('ext',new Node(9));return root;}
    case 30:Object.defineProperty(Node.prototype,'constructor',{enumerable:true});return root;
    case 31:Object.defineProperty(Node,'name',{writable:true});return root;
    case 32:{if(spec.kind==='list'&&root&&root.next){const d=root.next;root.next=d.next;d.next=trap('detached',d.next||root);}else{const x=any();if(x&&pool.length)x[f]=trap('child',pool[0]);}return root;} // Proxy only off the returned chain
    case 33:{const x=any();if(x&&pool.length)x[f]=trap('child',pool[0]);return 1;} // Proxy child, primitive result
   }
  };
  if(LANE==='t'&&pid===237){const inner=ns[spec.fn];ns[spec.fn]=function(node){const v=inner.call(this,node);return behaviour===26||r()<0.7?undefined:v;};}
  return {ns,cleanup(){Object.defineProperty(Object.prototype,'toString',{enumerable:false});Object.defineProperty(Function.prototype,'apply',{writable:true});if(saved)Object.prototype.valueOf=saved;for(const key of ['__eq_transient','__eq_call2','__eq_persist'])delete Object.prototype[key];delete Function.prototype.__eq_fp;}};
}

function argsFor(r,pid,spec,wire){
  const n=wire.values.length;
  if(LANE==='t'){
   if(pid===230)return [wire,r()<0.9?int(r,1,Math.max(1,n)):int(r,-1,n+2)];
   if(pid===235||pid===236){const p=int(r,0,Math.max(0,n-1));let q=int(r,0,Math.max(0,n-1));if(r()<0.9&&n>1&&q===p)q=(p+1)%n;return [wire,r()<0.95?p:n+1,q];}
   if(pid===237){let t=int(r,0,Math.max(0,n-1));if(r()<0.9){const tails=new Set(wire.next.map((v,i)=>v===null?i:-1));while(n>1&&tails.has(t))t=int(r,0,n-1);}return [wire,t];}
   return [wire];
  }
  if(pid===203)return [wire,int(r,1,50)];
  return [wire];
}

function run(mod,pid,args,seed,spec){
  const log=[],{ns,cleanup}=namespace(pid,spec,seed,log);let out;
  try{out=JSON.stringify(mod.observe(ns,pid,{args:JSON.parse(JSON.stringify(args))}));}catch(error){out='error:'+String(error).slice(0,300);}
  finally{cleanup();}
  return {out,log:log.join(',')};
}

const r=rng(SEED);let total=0,errors=0,proxyCases=0,mismatches=[];const outcomes={};
for(const [id,spec] of Object.entries(ROUTES)){
 const pid=Number(id);
 for(let c=0;c<CASES;c++){
  const big=c%97===0,n=Math.max(spec.min,Math.min(spec.lim,big?int(r,200,Math.min(spec.lim,3000)):int(r,0,24)));
  let wire=spec.kind==='tree'?treeWire(r,spec,n):listWire(r,spec,n);
  if(r()<0.12)wire=corrupt(r,wire,spec.kind);
  const args=argsFor(r,pid,spec,wire),seed=int(r,1,2**31);
  const a=run(v1,pid,args,seed,spec),b=run(v2,pid,args,seed,spec);total++;
  if(a.out.startsWith('error:'))errors++;if(a.log.includes(':gp')||a.log.includes(':ok'))proxyCases++;
  const tag=a.out.startsWith('error:')?a.out.slice(0,60):'record';outcomes[tag]=(outcomes[tag]||0)+1;
  if(a.out!==b.out||a.log!==b.log)mismatches.push({pid,c,seed,v1:a.out.slice(0,200),v2:b.out.slice(0,200),log_equal:a.log===b.log});
 }
}
// Unchanged class/scalar routes: a few direct controls through both harnesses.
const scalar=LANE==='t'?[[233,{countDigitOne:n=>6},[13]],[233,{countDigitOne:n=>({toJSON(){return 2;}})},[13]]]:[[214,{shortestPalindrome:s=>'a'+s},['ab']],[224,{calculate:s=>3},['1+2']],[212,{findWords:(b,w)=>w},[[['a']],['a']]]];
for(const [pid,ns,args] of scalar){const a=run({observe:(x,p,c)=>v1.observe(ns,p,c)},pid,args,1,{kind:'list',fn:'x'}),b=run({observe:(x,p,c)=>v2.observe(ns,p,c)},pid,args,1,{kind:'list',fn:'x'});total++;if(a.out!==b.out)mismatches.push({pid,v1:a.out,v2:b.out});}
const summary={schema:`gamma.${LANE}-observer-v1-v2-equivalence.v1`,lane:LANE,seed:SEED,cases_per_route:CASES,total_cases:total,v1_error_cases:errors,proxy_trap_cases:proxyCases,mismatches:mismatches.length,outcomes,candidate_executions:0};
process.stdout.write(JSON.stringify(summary)+'\n');
if(mismatches.length){process.stderr.write(JSON.stringify(mismatches.slice(0,10),null,1)+'\n');process.exitCode=1;}
