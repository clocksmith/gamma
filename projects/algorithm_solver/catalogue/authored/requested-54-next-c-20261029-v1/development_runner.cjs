"use strict";
const fs=require('fs'),path=require('path');
class TreeNode{constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}global.TreeNode=TreeNode;
function build(values){const nodes=values.map(v=>new TreeNode(v));for(let i=0;i<nodes.length;i++){if(2*i+1<nodes.length)nodes[i].left=nodes[2*i+1];if(2*i+2<nodes.length)nodes[i].right=nodes[2*i+2];}return nodes[0];}
function snapshot(root){const q=[root],out=[];for(let h=0;h<q.length;h++){const node=q[h];if(node===null){out.push(null);continue;}out.push(node.val);q.push(node.left,node.right);}while(out.length&&out[out.length-1]===null)out.pop();return out;}
function identities(value,set){if(value===null||typeof value!=='object')return;if(set.has(value))return;set.add(value);for(const v of Object.values(value))identities(v,set);}
const root=process.argv[2];
function invoke(c,official){const mod=require(path.join(root,'javascript',c.id+'.js')),args=JSON.parse(JSON.stringify(c.args)),before=JSON.stringify(args);let result;
 if(c.id===919){const [ops,rows]=args,original=build(rows[0][0]),receiver=new mod.CBTInserter(original),originalBefore=JSON.stringify(original),inputNodes=new Set();identities(original,inputNodes);result=[null];let stableRoot=null;
  for(let i=1;i<ops.length;i++){const value=receiver[ops[i]](...rows[i]);if(ops[i]==='get_root'){if(stableRoot!==null&&stableRoot!==value)throw Error('unstable root');stableRoot=value;const outputNodes=new Set();identities(value,outputNodes);for(const x of outputNodes)if(inputNodes.has(x))throw Error('constructor input alias');result.push(snapshot(value));}else result.push(value);}
  if(JSON.stringify(original)!==originalBefore)throw Error('constructor input mutation');
 }else if(c.id===933){const [ops,rows]=args,receiver=new mod.RecentCounter();result=[null];for(let i=1;i<ops.length;i++)result.push(receiver[ops[i]](...rows[i]));}
 else{result=(official?mod[c.name]:mod)(...args);if(result&&typeof result==='object'){const inputIds=new Set(),outputIds=new Set();identities(args,inputIds);identities(result,outputIds);for(const x of outputIds)if(inputIds.has(x))throw Error('output input alias');}}
 if(JSON.stringify(args)!==before)throw Error('input mutation');return result;
}
const cases=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(cases.map(c=>{try{return{result:invoke(c,false),wrapper:invoke(c,true)}}catch(e){return{error:e.stack}}})));
