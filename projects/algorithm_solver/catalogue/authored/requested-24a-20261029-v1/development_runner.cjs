"use strict";
const fs=require('fs'),path=require('path');const root=process.argv[2];
class TreeNode{constructor(val,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
function tree(flat){const nodes=flat.map(row=>new TreeNode(row[0]));for(let i=0;i<flat.length;i++){nodes[i].left=flat[i][1]===null?null:nodes[flat[i][1]];nodes[i].right=flat[i][2]===null?null:nodes[flat[i][2]];}return nodes[0];}
function snapshot(node){const q=[node],seen=new Map([[node,0]]),rows=[];for(let i=0;i<q.length;i++){const n=q[i];const indices=[];for(const child of [n.left,n.right]){if(child===null)indices.push(null);else{if(!seen.has(child)){seen.set(child,q.length);q.push(child);}indices.push(seen.get(child));}}rows.push([n.val,...indices]);}return rows;}
function identities(value,set,unique=false){if(value===null||typeof value!=='object')return;if(set.has(value)){if(unique)throw Error('mutable alias');return;}set.add(value);for(const x of Object.values(value))identities(x,set,unique);}
function run(c,official=false){let args=JSON.parse(JSON.stringify(c.args));const original=JSON.stringify(args),mod=require(path.join(root,'javascript',c.id+'.js'));let output;
 if(c.id===1530){const node=tree(args[0]),before=JSON.stringify(snapshot(node));output=(official?mod.countPairs:mod)(node,args[1]);if(JSON.stringify(snapshot(node))!==before)throw Error('tree mutation');}
 else{const [ops,rows]=args,name=c.id===1600?'ThroneInheritance':'ParkingSystem',receiver=new mod[name](...rows[0]);output=[null];for(let i=1;i<ops.length;i++){const value=receiver[ops[i]](...rows[i]);if(['birth','death'].includes(ops[i])&&value!==undefined)throw Error('void method return');output.push(value===undefined?null:value);}}
 if(JSON.stringify(args)!==original)throw Error('input mutation');const inputs=new Set(),outputs=new Set();identities(args,inputs);identities(output,outputs,true);for(const value of outputs)if(inputs.has(value))throw Error('input-output alias');return output;
}
const cases=JSON.parse(fs.readFileSync(0,'utf8'));const result=cases.map(c=>{try{return {result:run(c),wrapper:c.id===1530?run(c,true):null};}catch(error){return {error:error.stack};}});process.stdout.write(JSON.stringify(result));
