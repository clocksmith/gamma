'use strict';
// T native graph helper v2. It performs the checks of
// continuation-t-observers-20261028-v1/native_graphs.cjs with the same records
// and error text, restructured for --jitless interpreter cost (README.md).
//
// Rules that keep v2 equal to v1:
// 1. Any object that is a Proxy is handled by the verbatim v1 code below, so
//    every trap fires in v1's order. util.types.isProxy runs no user code.
// 2. For ordinary objects, descriptor and prototype reads run no user code.
//    v2 may skip repeated reads or read per key without changing a result.
// 3. A fast check that fails reruns the verbatim v1 check. v1 then supplies
//    the thrown error, so error text and precedence stay v1's.
const {isProxy}=require('util').types;

// ---- Verbatim v1 code (authority for Proxy objects and every failure) ----
function v1Guard(objects){
  return()=>{for(const {object,prototype,descriptors} of objects){const now=Object.getOwnPropertyDescriptors(object),keys=Reflect.ownKeys(descriptors);if(Object.getPrototypeOf(object)!==prototype||Reflect.ownKeys(now).length!==keys.length)throw TypeError('original prototype changed');for(const key of keys){const a=descriptors[key],b=now[key];if(!b||Reflect.ownKeys(a).length!==Reflect.ownKeys(b).length||Reflect.ownKeys(a).some(k=>a[k]!==b[k]))throw TypeError('original class descriptor changed');}}};
}
function v1Data(graph,node){if(node===null||typeof node!=='object'||Object.getPrototypeOf(node)!==graph.prototype)throw TypeError('original source node prototype');const descriptors=Object.getOwnPropertyDescriptors(node),keys=Reflect.ownKeys(descriptors),data={};let flags=0,shift=0;if(keys.length!==graph.fields.length||graph.fields.some(k=>!Object.hasOwn(descriptors,k)))throw TypeError('exact own native fields');for(const key of graph.fields){const d=descriptors[key];if(!Object.hasOwn(d,'value'))throw TypeError('own native data field');data[key]=d.value;flags|=((d.writable?1:0)|(d.enumerable?2:0)|(d.configurable?4:0))<<shift;shift+=3;}if(!Number.isSafeInteger(data.val))throw TypeError('exact integer nodevalue');if(graph.flags.has(node)){if(graph.flags.get(node)!==flags)throw TypeError('native own descriptors changed');}else graph.flags.set(node,flags);return data;}
function v1Snapshot(graph){graph.guard();return graph.nodes.map(node=>{const d=graph.data(node),row={value:d.val};for(const field of graph.fields.slice(1))row[field]=graph.identify(d[field],true);return row;});}

// ---- Class/prototype guard ----
function classGuard(cls){
  if(typeof cls!=='function'||!cls.prototype)throw TypeError('original exported constructor required');
  const objects=[];for(const first of [cls,cls.prototype])for(let object=first;object!==null;object=Object.getPrototypeOf(object))if(!objects.some(r=>r.object===object))objects.push({object,prototype:Object.getPrototypeOf(object),descriptors:Object.getOwnPropertyDescriptors(object)});
  const exact=v1Guard(objects);
  // A Proxy anywhere on the chain makes every guard call run candidate code:
  // use v1's guard verbatim and tell the Graph (see proxyChain below).
  if(objects.some(r=>isProxy(r.object))){exact.proxyChain=true;return exact;}
  // Flatten the frozen descriptors once into one array per object:
  // [key, isData, value|get, writable|undefined, enumerable, configurable, undefined|set, ...].
  // A data descriptor is {value,writable,enumerable,configurable}; an accessor is {get,set,enumerable,configurable}.
  const rows=objects.map(({object,prototype,descriptors})=>{
    const keys=Reflect.ownKeys(descriptors),flat=[];
    for(const key of keys){const a=descriptors[key],isData=Object.hasOwn(a,'value');flat.push(key,isData,isData?a.value:a.get,isData?a.writable:undefined,a.enumerable,a.configurable,isData?undefined:a.set);}
    return [object,prototype,keys.length,flat];
  });
  const passes=()=>{ // returns true only when v1's guard would also pass
    for(let r=0;r<rows.length;r++){
      const row=rows[r],object=row[0],flat=row[3];
      if(Object.getPrototypeOf(object)!==row[1]||Reflect.ownKeys(object).length!==row[2])return false;
      for(let i=0;i<flat.length;i+=7){
        const b=Object.getOwnPropertyDescriptor(object,flat[i]);
        // b is a fresh complete descriptor. A boolean writable exists only on data
        // descriptors, so writable alone tells data from accessor. Any lookup that
        // falls through to a changed Object.prototype still returns false: that
        // object is itself a row of this same check.
        if(b===undefined||b.enumerable!==flat[i+4]||b.configurable!==flat[i+5]||b.writable!==flat[i+3])return false;
        if(flat[i+1]?b.value!==flat[i+2]:b.get!==flat[i+2]||b.set!==flat[i+6])return false;
      }
    }
    return true;
  };
  return()=>{if(!passes())exact();};
}

function object(value,keys){return value!==null&&typeof value==='object'&&!Array.isArray(value)&&Reflect.ownKeys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));}

class Graph{
 constructor(cls,kind,limit,required=false){this.cls=cls;this.prototype=cls?.prototype;this.guard=classGuard(cls);this.kind=kind;this.limit=limit;this.fields=kind==='list'?['val','next']:['val','left','right'];this.tree=kind!=='list';this.nodes=[];this.ids=new Map();this.flags=new Map();this.external=new Map();this.plain=true;this.foreign=0;if(this.guard.proxyChain){const exact=this.guard;this.plain=false;this.guard=()=>{this.foreign++;exact();};}const probe=required?new cls(0):new cls();this.guard();const d=this.data(probe);if(d.val!==0||this.fields.slice(1).some(k=>d[k]!==null))throw Error('exact original constructor defaults');}
 data(node){
  if(node===null||typeof node!=='object'||isProxy(node)){if(node!==null&&typeof node==='object')this.foreign++;return v1Data(this,node);}
  if(Object.getPrototypeOf(node)!==this.prototype)throw TypeError('original source node prototype');
  const fail=()=>v1Data(this,node);
  if(this.tree){
   if(Reflect.ownKeys(node).length!==3)return fail();
   const v=Object.getOwnPropertyDescriptor(node,'val'),l=Object.getOwnPropertyDescriptor(node,'left'),r=Object.getOwnPropertyDescriptor(node,'right');
   if(v===undefined||l===undefined||r===undefined||!Object.hasOwn(v,'value')||!Object.hasOwn(l,'value')||!Object.hasOwn(r,'value')||!Number.isSafeInteger(v.value))return fail();
   const flags=(v.writable?1:0)|(v.enumerable?2:0)|(v.configurable?4:0)|((l.writable?1:0)|(l.enumerable?2:0)|(l.configurable?4:0))<<3|((r.writable?1:0)|(r.enumerable?2:0)|(r.configurable?4:0))<<6;
   const old=this.flags.get(node);if(old===undefined)this.flags.set(node,flags);else if(old!==flags)return fail();
   return {val:v.value,left:l.value,right:r.value};
  }
  if(Reflect.ownKeys(node).length!==2)return fail();
  const v=Object.getOwnPropertyDescriptor(node,'val'),n=Object.getOwnPropertyDescriptor(node,'next');
  if(v===undefined||n===undefined||!Object.hasOwn(v,'value')||!Object.hasOwn(n,'value')||!Number.isSafeInteger(v.value))return fail();
  const flags=(v.writable?1:0)|(v.enumerable?2:0)|(v.configurable?4:0)|((n.writable?1:0)|(n.enumerable?2:0)|(n.configurable?4:0))<<3;
  const old=this.flags.get(node);if(old===undefined)this.flags.set(node,flags);else if(old!==flags)return fail();
  return {val:v.value,next:n.value};
 }
 construct(value){if(!Number.isSafeInteger(value))throw TypeError('integer node value');const node=new this.cls(value);this.guard();const d=this.data(node);if(this.ids.has(node)||d.val!==value||(this.tree?d.left!==null||d.right!==null:d.next!==null))throw Error('fresh original constructor defaults');if(this.nodes.length>=this.limit)throw Error('native node envelope');if(isProxy(node))this.plain=false;this.ids.set(node,this.nodes.length);this.nodes.push(node);return node;}
 identify(node,external=false){if(node===null)return null;this.data(node);if(this.ids.has(node))return this.ids.get(node);if(!external)throw Error('result must use original identity');if(!this.external.has(node))this.external.set(node,this.external.size);return {external_identity:this.external.get(node)};}
 // v1 also re-validated each pool child via identify(child)->data(child). With
 // ordinary pool nodes that read is pure and repeats the child's own row check
 // in the same pass, so it cannot change success. On any failure, or on a Proxy
 // child, the verbatim v1 snapshot reruns from the start and decides.
 snapshot(){
  if(!this.plain)return v1Snapshot(this);
  // plain implies no Proxy on the class chain, so this guard is pure. Its errors
  // propagate exactly once, as in v1; only the node pass below may fall back.
  this.guard();
  const foreign=this.foreign;let rows;
  try{rows=this.fastRows();}catch(error){rows=null;}
  if(rows===null||this.foreign!==foreign)return v1Snapshot(this); // reruns the pure guard, then v1's rows
  return rows;
 }
 fastRows(){
  const nodes=this.nodes,ids=this.ids,count=nodes.length,rows=new Array(count);
  const child=value=>{if(value===null)return null;const id=ids.get(value);if(id!==undefined)return id;if(value!==null&&typeof value==='object'&&isProxy(value))throw ABORT;return this.identify(value,true);};
  if(this.tree)for(let i=0;i<count;i++){const d=this.data(nodes[i]);rows[i]={value:d.val,left:child(d.left),right:child(d.right)};}
  else for(let i=0;i<count;i++){const d=this.data(nodes[i]);rows[i]={value:d.val,next:child(d.next)};}
  return rows;
 }
 linked(root){const order=[],seen=new Set();for(let node=root;node!==null;node=this.data(node).next){const index=this.identify(node);if(seen.has(index))throw Error('returned list cycle');seen.add(index);order.push(index);}return {head:this.identify(root),order,values:order.map(i=>this.data(this.nodes[i]).val)};}
}
const ABORT=Symbol('proxy child: rerun v1 snapshot');
// build is byte-for-byte the v1 function body.
function build(graph,pid,wire){const tree=[226,230,235,236].includes(pid),keys=tree?['values','left','right','root']:['values','next','head'];if(!object(wire,keys)||!Array.isArray(wire.values))throw Error('exact indexed T native model');const values=wire.values,n=values.length,minimum=pid===226?0:[230,234].includes(pid)?1:2;if(n<minimum||n>graph.limit)throw Error('native size bound');const [low,high]=pid===226?[-100,100]:pid===230?[0,10000]:[235,236].includes(pid)?[-1000000000,1000000000]:pid===234?[0,9]:[-1000,1000];if(values.some(v=>!Number.isSafeInteger(v)||v<low||v>high))throw Error('native value domain');if([230,235,236,237].includes(pid)&&new Set(values).size!==n)throw Error('unique original values');const valid=index=>index===null||Number.isInteger(index)&&index>=0&&index<n,fields=tree?['left','right']:['next'],root=wire[tree?'root':'head'];if(!valid(root)||(root===null)!==(n===0))throw Error('native root');for(const field of fields)if(!Array.isArray(wire[field])||wire[field].length!==n||wire[field].some(v=>!valid(v)))throw Error('native edge indices');const seen=new Set(),queue=root===null?[]:[root];for(let head=0;head<queue.length;head++){const i=queue[head];if(seen.has(i))throw Error('original cycle/alias');seen.add(i);for(const field of fields)if(wire[field][i]!==null)queue.push(wire[field][i]);}if(seen.size!==n)throw Error('unreachable original nodes');if([230,235].includes(pid)){const pending=[];let current=root,previous=null;while(current!==null||pending.length){while(current!==null){pending.push(current);current=wire.left[current];}current=pending.pop();if(previous!==null&&previous>=values[current])throw Error('strict BST required');previous=values[current];current=wire.right[current];}}const nodes=values.map(value=>graph.construct(value));for(let i=0;i<n;i++)for(const field of fields)nodes[i][field]=wire[field][i]===null?null:nodes[wire[field][i]];return root===null?null:nodes[root];}
module.exports={classGuard,object,Graph,build};
