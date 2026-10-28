'use strict';
// Original-source official wrapper observer; no expected outputs or injected classes.
const fs=require('fs');
const METHODS={17:'letterCombinations',37:'solveSudoku',65:'isNumber',87:'isScramble',95:'generateTrees',99:'recoverTree',108:'sortedArrayToBST',114:'flatten',116:'connect',117:'connect'};
const TREE=new Set([95,99,108,114,116,117]),VOID=new Set([37,99,114]),MAX_NODES=20000;
const clone=value=>JSON.parse(JSON.stringify(value));
function classGuard(cls){
  if(typeof cls!=='function'||!cls.prototype)throw TypeError('original exported constructor required');
  const objects=[];for(const first of [cls,cls.prototype])for(let object=first;object!==null;object=Object.getPrototypeOf(object))if(!objects.some(row=>row.object===object))objects.push({object,prototype:Object.getPrototypeOf(object),descriptors:Object.getOwnPropertyDescriptors(object)});
  return()=>{for(const {object,prototype,descriptors} of objects){const now=Object.getOwnPropertyDescriptors(object),keys=Reflect.ownKeys(descriptors);if(Object.getPrototypeOf(object)!==prototype||Reflect.ownKeys(now).length!==keys.length)throw TypeError('original prototype changed');for(const key of keys){const a=descriptors[key],b=now[key];if(!b||Reflect.ownKeys(a).some(field=>a[field]!==b[field])||Reflect.ownKeys(a).length!==Reflect.ownKeys(b).length)throw TypeError('original class descriptor changed');}}};
}
class Graph{
  constructor(cls,nextFields=false){this.cls=cls;this.prototype=cls.prototype;this.guard=classGuard(cls);this.fields=nextFields?['val','left','right','next']:['val','left','right'];this.nodes=[];this.ids=new Map();this.flags=new Map();}
  data(node){
    if(node===null||typeof node!=='object'||Object.getPrototypeOf(node)!==this.prototype)throw TypeError('original source node prototype required');
    const descriptors=Object.getOwnPropertyDescriptors(node),keys=Reflect.ownKeys(descriptors);
    if(keys.length!==this.fields.length||this.fields.some(field=>!Object.hasOwn(descriptors,field)))throw TypeError('original own node fields required');
    const data={},flags={};for(const field of this.fields){const d=descriptors[field];if(!Object.hasOwn(d,'value'))throw TypeError('node own data field required');data[field]=d.value;flags[field]=[d.writable,d.enumerable,d.configurable];}
    if(!Number.isSafeInteger(data.val))throw TypeError('exact safe integer node value required');
    if(this.flags.has(node)){const before=this.flags.get(node);if(this.fields.some(field=>before[field].some((v,i)=>v!==flags[field][i])))throw TypeError('original own field flags changed');}else this.flags.set(node,flags);
    return data;
  }
  identify(node){if(node===null)return null;this.data(node);if(!this.ids.has(node)){if(this.nodes.length>=MAX_NODES)throw Error('observer node envelope exceeded');this.ids.set(node,this.nodes.length);this.nodes.push(node);}return this.ids.get(node);}
  snapshot(){
    this.guard();const rows=[];for(const node of this.nodes){const data=this.data(node),row={id:this.ids.get(node),value:data.val};for(const field of this.fields.slice(1))row[field]=this.identify(data[field]);rows.push(row);}
    const colors=new Map();for(let start=0;start<rows.length;start++){const todo=[[start,false]];while(todo.length){const [index,leaving]=todo.pop();if(leaving){colors.set(index,2);continue;}if(colors.get(index)===1)throw Error('detached or reachable node cycle');if(colors.get(index)===2)continue;colors.set(index,1);todo.push([index,true]);for(const field of ['right','left'])if(rows[index][field]!==null)todo.push([rows[index][field],false]);}}
    if(this.fields.includes('next')){const done=new Set();for(let start=0;start<rows.length;start++){const path=new Set();let current=start;while(current!==null&&!done.has(current)){if(path.has(current))throw Error('next-pointer cycle');path.add(current);current=rows[current].next;}for(const id of path)done.add(id);}}
    return rows;
  }
  tree(root,marker){
    if(root===null)return {[marker]:[]};const queue=[root],seen=new Set(),values=[];
    for(let i=0;i<queue.length;i++){const node=queue[i];if(node===null){values.push(null);continue;}if(seen.has(node))throw Error('cycle or internal tree alias');seen.add(node);this.identify(node);const data=this.data(node);values.push(data.val);queue.push(data.left,data.right);}
    while(values.length&&values.at(-1)===null)values.pop();return {[marker]:values};
  }
}
function buildTree(graph,wire,marker){
  if(wire===null||typeof wire!=='object'||Array.isArray(wire)||Object.keys(wire).join(',')!==marker||!Array.isArray(wire[marker]))throw Error('exact tree marker required');
  const values=wire[marker];if(!values.length)return null;if(values.length>2*MAX_NODES+1||!Number.isSafeInteger(values[0]))throw Error('bounded integer root required');
  const root=new graph.cls(values[0]),queue=[root];let index=1;
  for(let i=0;i<queue.length;i++){const parent=queue[i];for(const field of ['left','right']){if(index>=values.length)break;const value=values[index++];if(value!==null){if(!Number.isSafeInteger(value))throw TypeError('integer node value required');const child=new graph.cls(value);parent[field]=child;queue.push(child);}}if(queue.length>MAX_NODES)throw Error('input tree envelope exceeded');}
  if(index!==values.length)throw Error('unreachable tree slots');if(graph.fields.includes('next')&&queue.some(node=>graph.data(node).next!==null))throw Error('initial next pointers must be null');graph.tree(root,marker);return root;
}
function observe(namespace,pid,call){
  if(!Number.isInteger(pid)||!Object.hasOwn(METHODS,pid)||call===null||typeof call!=='object'||Object.keys(call).join(',')!=='args'||!Array.isArray(call.args))throw Error('fixed argument-only official wrapper call required');
  if(call.args.length!==(pid===87?2:1))throw Error('exact official argument arity required');
  let args=clone(call.args);const before=clone(args),solution=namespace.Solution,solutionGuard=classGuard(solution);let graph=null,root=null,argumentRoots=[],beforeNodes=[];
  const descriptor=Object.getOwnPropertyDescriptor(solution.prototype,METHODS[pid]);if(!descriptor||typeof descriptor.value!=='function')throw TypeError('original official method required; no solve fallback');
  const marker=[116,117].includes(pid)?'__next_node__':'__tree_node__';
  if(TREE.has(pid)){graph=new Graph(namespace[[116,117].includes(pid)?'Node':'TreeNode'],[116,117].includes(pid));if([99,114,116,117].includes(pid)){if(args.length!==1)throw Error('one original tree argument required');root=buildTree(graph,args[0],marker);args=[root];argumentRoots=[graph.identify(root)];beforeNodes=graph.snapshot();}}
  const receiver=new solution();if(Object.getPrototypeOf(receiver)!==solution.prototype)throw TypeError('original Solution receiver required');
  const board=pid===37?args[0]:null,result=Reflect.apply(descriptor.value,receiver,args);solutionGuard();if(VOID.has(pid)&&result!==undefined)throw TypeError('official void method must return undefined');
  const record={native_route:'official-wrapper-p-v1',problem_id:pid,method:METHODS[pid],result:null,result_type:typeof result,args_before:before,args_after:null,alias_edges:[],node_identity:null,node_integrity:null,board_identity:null};
  if(graph===null){record.result=result===undefined?null:clone(result);record.args_after=clone(args);if(pid===37){if(args[0]!==board||!Array.isArray(board)||board.length!==9||board.some(row=>!Array.isArray(row)||row.length!==9))throw Error('original board root/shape changed');record.board_identity={argument_root_preserved:true,before_shape:[9,9],after_shape:[9,9]};}return record;}
  let resultRoot=null,resultRoots=[];
  if(pid===95){if(!Array.isArray(result)||result.length>2000)throw TypeError('bounded actual node forest required');record.result=result.map(node=>graph.tree(node,marker));resultRoots=result.map(node=>graph.identify(node));record.args_after=clone(args);}
  else if(pid===108){record.result=graph.tree(result,marker);resultRoot=graph.identify(result);record.args_after=clone(args);}
  else{record.args_after=[graph.tree(root,marker)];if([116,117].includes(pid)){if(result!==root)throw Error('connect must return original root');record.result=graph.tree(result,marker);resultRoot=graph.identify(result);if(root!==null)record.alias_edges=[['result','args.0']];}}
  const after=graph.snapshot();graph.guard();record.node_identity={before:beforeNodes,after,argument_roots:argumentRoots,result_root:resultRoot,result_roots:resultRoots};record.node_integrity={schema:'gamma.p-official-node-integrity.v1',class_or_prototype_unchanged:true,own_field_descriptors_unchanged:true,original_node_classes_unchanged:true,acyclic_tree_graphs:true,forest_cross_tree_aliases_permitted:pid===95,checked_node_count:graph.nodes.length};return record;
}
function main(){const packet=JSON.parse(fs.readFileSync('inputs.json','utf8'));if(packet===null||typeof packet!=='object'||Object.keys(packet).sort().join(',')!=='calls,problem_id,schema'||packet.schema!=='gamma.p-official-wrapper-packet.v1'||!Number.isInteger(packet.problem_id)||!Object.hasOwn(METHODS,packet.problem_id)||!Array.isArray(packet.calls))throw Error('fixed P official packet required');const namespace=require('./program.cjs');for(let i=0;i<packet.calls.length;i++){let record;try{record={i,...observe(namespace,packet.problem_id,packet.calls[i])};}catch(error){record={i,error:String(error).slice(0,300)};}process.stdout.write(JSON.stringify(record)+'\n');}process.stdout.write(JSON.stringify({done:packet.calls.length})+'\n');}
if(require.main===module)main();module.exports={METHODS,Graph,buildTree,observe};
