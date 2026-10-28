'use strict';
const fs=require('fs'),{classGuard,Graph,build,object}=require('./native_graphs.cjs');
const clone=x=>JSON.parse(JSON.stringify(x));
function exportGuard(namespace,name){const before=Object.getOwnPropertyDescriptor(namespace,name);if(!before||!Object.hasOwn(before,'value')||typeof before.value!=='function')throw TypeError('original own function export');const value=before.value,guard=classGuard(value);return{value,check(){guard();const after=Object.getOwnPropertyDescriptor(namespace,name);if(!after||Reflect.ownKeys(before).length!==Reflect.ownKeys(after).length||Reflect.ownKeys(before).some(k=>before[k]!==after[k]))throw TypeError('original export descriptor changed');}};}
function observe(namespace,pid,call){
 if(!Number.isInteger(pid)||pid!==257||!object(call,['args'])||!Array.isArray(call.args)||call.args.length!==1)throw Error('fixed U257 argument-only call');
 const args=clone(call.args),before=clone(args),binding=exportGuard(namespace,'binaryTreePaths'),nodeBinding=exportGuard(namespace,'TreeNode'),graph=new Graph(nodeBinding.value,'tree',100),root=build(graph,pid,args[0]),initial=graph.snapshot();
 const value=Reflect.apply(binding.value,undefined,[root]);binding.check();nodeBinding.check();graph.guard();
 if(!Array.isArray(value)||value.some(v=>typeof v!=='string'))throw TypeError('array of strings required');
 return {native_route:'official-u-v1',problem_id:pid,method:'binaryTreePaths',entry_kind:'javascript-official-function',result:clone(value),result_type:'object',args_before:before,args_after:clone(args),alias_edges:[],
 node_identity:{before:initial,after:graph.snapshot(),argument_roots:[graph.identify(root)],fixture_roots:[],result_root:null,result_order:null},
 node_integrity:{schema:'gamma.u-native-integrity.v1',class_or_prototype_unchanged:true,own_field_descriptors_unchanged:true,original_node_classes_unchanged:true,checked_node_count:graph.nodes.length,native_aliases_in_identity_table:true},
 entry_integrity:{schema:'gamma.u-entry-integrity.v1',original_export_unchanged:true,class_or_prototype_unchanged:true,method_descriptor_unchanged:true,fresh_receiver:null}};
}
function main(){const p=JSON.parse(fs.readFileSync('inputs.json','utf8'));if(!object(p,['schema','problem_id','calls'])||p.schema!=='gamma.u-official-packet.v1'||!Number.isInteger(p.problem_id)||p.problem_id!==257||!Array.isArray(p.calls)||p.calls.length<1||p.calls.length>33)throw Error('fixed U257 packet');const ns=require('./program.cjs');for(let i=0;i<p.calls.length;i++){let row;try{row={i,...observe(ns,p.problem_id,p.calls[i])};}catch(e){row={i,error:String(e).slice(0,300)};}process.stdout.write(JSON.stringify(row)+'\n');}process.stdout.write(JSON.stringify({done:p.calls.length})+'\n');}
if(require.main===module)main();module.exports={observe};
