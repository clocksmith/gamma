"use strict";
// S observer harness v2: continuation-s-observers-20261028-v1/harness.cjs with one change.
// v1 took a post-call snapshot, handled the result, then took the snapshot again and kept the second.
// v2 keeps the first when neither it nor anything after it could run candidate code (plain graph:
// no Proxy node or class chain; no Proxy reached; and, on the clone(value) branch, no object/function/bigint result), so the second would be equal.
const fs=require('fs'),{classGuard,Graph,build,object}=require('./native_graphs.cjs');
const IDS=[199,203,206,208,211,212,214,222,224,225],METHODS={199:'rightSideView',203:'removeElements',206:'reverseList',212:'findWords',214:'shortestPalindrome',222:'countNodes',224:'calculate'},CLASSES={208:['Trie',{insert:1,search:1,startsWith:1},['insert'],30000],211:['WordDictionary',{addWord:1,search:1},['addWord'],10000],225:['MyStack',{push:1,pop:0,top:0,empty:0},['push'],100]},SEEN=new WeakSet();
const clone=value=>JSON.parse(JSON.stringify(value));
function fresh(receiver){if(SEEN.has(receiver))throw TypeError('original receiver reused');SEEN.add(receiver);}
function exportGuard(namespace,name){const before=Object.getOwnPropertyDescriptor(namespace,name);if(!before||!Object.hasOwn(before,'value')||typeof before.value!=='function')throw TypeError('original own exported function/class required');const value=before.value,guard=classGuard(value);return {value,check(){guard();const after=Object.getOwnPropertyDescriptor(namespace,name);if(!after||Reflect.ownKeys(before).length!==Reflect.ownKeys(after).length||Reflect.ownKeys(before).some(key=>before[key]!==after[key]))throw TypeError('original export descriptor changed');}};}
function aliases(args,result){const originals=new Map(),seen=new Set(),todo=args.map((value,i)=>[value,`args.${i}`]);while(todo.length){const [value,path]=todo.pop();if(value===null||typeof value!=='object'||seen.has(value))continue;seen.add(value);originals.set(value,path);for(const key of Object.keys(value))todo.push([value[key],`${path}.${key}`]);}const edges=[],visited=new Set(),pending=[[result,'result']];while(pending.length){const [value,path]=pending.pop();if(value===null||typeof value!=='object'||visited.has(value))continue;visited.add(value);if(originals.has(value))edges.push([path,originals.get(value)]);for(const key of Object.keys(value))pending.push([value[key],`${path}.${key}`]);}return edges.sort();}
function observe(namespace,pid,call){
 if(!Number.isInteger(pid)||!IDS.includes(pid)||!object(call,['args'])||!Array.isArray(call.args))throw Error('fixed S argument-only call');
 const args=clone(call.args),beforeArgs=clone(args),record={native_route:'official-s-v1',problem_id:pid,method:null,entry_kind:null,result:null,result_type:null,args_before:beforeArgs,args_after:null,alias_edges:[],node_identity:null,node_integrity:null,entry_integrity:{schema:'gamma.s-entry-integrity.v1',original_export_unchanged:true,class_or_prototype_unchanged:true,method_descriptor_unchanged:true,fresh_receiver:Object.hasOwn(CLASSES,pid)?true:null},native_class:null,native_receiver_count:null,native_method_return_types:null,native_method_snapshots:null};
 if(Object.hasOwn(CLASSES,pid)){
  const [name,methods,voidMethods,limit]=CLASSES[pid];if(args.length!==2||!Array.isArray(args[0])||!Array.isArray(args[1])||args[0].length!==args[1].length||!args[0].length||args[0][0]!==name||!Array.isArray(args[1][0])||args[1][0].length!==0||args[0].length-1>limit||args[1].some(row=>!Array.isArray(row)))throw Error('one bounded constructor trace');
  const binding=exportGuard(namespace,name),cls=binding.value,receiver=new cls();binding.check();if(Object.getPrototypeOf(receiver)!==cls.prototype)throw TypeError('original design receiver prototype');fresh(receiver);
  const outputs=[null],types=['constructed'],snapshots=[null];
  for(let i=1;i<args[0].length;i++){
   const method=args[0][i],row=args[1][i];if(typeof method!=='string'||!Object.hasOwn(methods,method)||row.length!==methods[method])throw Error('declared own method arity');
   if(Object.hasOwn(receiver,method))throw TypeError('receiver may not shadow original prototype method');const descriptor=Object.getOwnPropertyDescriptor(cls.prototype,method);if(!descriptor||!Object.hasOwn(descriptor,'value')||typeof descriptor.value!=='function')throw TypeError('original own prototype method required');
   const value=Reflect.apply(descriptor.value,receiver,row);if(Object.getPrototypeOf(receiver)!==cls.prototype)throw TypeError('receiver prototype changed');
   if(voidMethods.includes(method)){if(value!==undefined)throw TypeError('official void returns undefined');}else if(pid===208||pid===211||method==='empty'){if(typeof value!=='boolean')throw TypeError('exact native boolean return');}else if(!Number.isSafeInteger(value))throw TypeError('exact native integer return');
   binding.check();if(Object.keys(methods).some(name=>Object.hasOwn(receiver,name)))throw TypeError('receiver shadows original prototype method');outputs.push(value===undefined?null:value);types.push(typeof value);snapshots.push(value===undefined?null:clone(value));
  }
  Object.assign(record,{entry_kind:'javascript-native-class',result:outputs,result_type:'object',native_class:name,native_receiver_count:1,native_method_return_types:types,native_method_snapshots:snapshots});
 }else{
  const arity=[203,212].includes(pid)?2:1;if(args.length!==arity)throw Error('official function arity');const method=METHODS[pid],binding=exportGuard(namespace,method),fn=binding.value;let graph=null,root=null,initial=[],nodeBinding=null,nativeArgs=args;
  if([199,203,206,222].includes(pid)){const name=[199,222].includes(pid)?'TreeNode':'ListNode';nodeBinding=exportGuard(namespace,name);graph=new Graph(nodeBinding.value,[199,222].includes(pid)?'tree':'list',({199:100,203:10000,206:5000,222:50000})[pid]);root=build(graph,pid,args[0]);initial=graph.snapshot();nativeArgs=[root,...args.slice(1)];}
  const value=Reflect.apply(fn,undefined,nativeArgs);binding.check();Object.assign(record,{method,entry_kind:'javascript-official-function',result_type:typeof value});
  if(graph){
   graph.guard();nodeBinding.check();const mark=graph.foreign;let after=graph.snapshot(),resultRoot=null,order=null;const quiet=graph.plain&&([203,206].includes(pid)||value===null||!['object','function','bigint'].includes(typeof value));
   if([203,206].includes(pid)){const normalized=graph.linked(value);resultRoot=normalized.head;order=normalized.order;record.result=normalized;if(resultRoot!==null)record.alias_edges=[['result',`args.0.pool.${resultRoot}`]];}else record.result=clone(value);
   if(!quiet||graph.foreign!==mark){graph.guard();after=graph.snapshot();}record.node_identity={before:initial,after,argument_roots:[graph.identify(root)],result_root:resultRoot,result_order:order};record.node_integrity={schema:'gamma.s-native-integrity.v1',class_or_prototype_unchanged:true,own_field_descriptors_unchanged:true,original_node_classes_unchanged:true,checked_node_count:graph.nodes.length,native_aliases_in_identity_table:true};
  }else{record.alias_edges=aliases(args,value);record.result=clone(value);}
 }
 record.args_after=clone(args);return record;
}
function main(){const packet=JSON.parse(fs.readFileSync('inputs.json','utf8'));if(!object(packet,['schema','problem_id','calls'])||packet.schema!=='gamma.s-official-packet.v1'||!Number.isInteger(packet.problem_id)||!IDS.includes(packet.problem_id)||!Array.isArray(packet.calls)||packet.calls.length<1||packet.calls.length>33)throw Error('fixed S official packet');const namespace=require('./program.cjs');for(let i=0;i<packet.calls.length;i++){let record;try{record={i,...observe(namespace,packet.problem_id,packet.calls[i])};}catch(error){record={i,error:String(error).slice(0,300)};}process.stdout.write(JSON.stringify(record)+'\n');}process.stdout.write(JSON.stringify({done:packet.calls.length})+'\n');}
if(require.main===module)main();module.exports={IDS,METHODS,CLASSES,observe};
