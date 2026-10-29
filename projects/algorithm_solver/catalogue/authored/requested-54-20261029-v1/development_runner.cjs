"use strict";
const fs=require('fs'),path=require('path');
class TreeNode{constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
global.TreeNode=TreeNode;
const root=process.argv[2];
function tree(t){return t===null?null:new TreeNode(t[0],tree(t[1]),tree(t[2]));}
function encode(t){return t===null?null:[t.val,encode(t.left),encode(t.right)];}
function identities(value,set,unique=false){if(value===null||typeof value!=='object')return;if(set.has(value)){if(unique)throw Error('mutable output alias');return;}set.add(value);for(const x of Object.values(value))identities(x,set,unique);}
function invoke(c,official){const mod=require(path.join(root,'javascript',c.id+'.js'));let args=JSON.parse(JSON.stringify(c.args));if(c.id===872)args=args.map(tree);const before=JSON.stringify(args),inputs=new Set();identities(args,inputs);let result;
 if(c.id===895){const [ops,rows]=args,receiver=new mod.FreqStack(...rows[0]);result=[null];for(let i=1;i<ops.length;i++){const value=receiver[ops[i]](...rows[i]);if(ops[i]==='push'&&value!==undefined)throw Error('void return');result.push(value===undefined?null:value);}}
 else{const fn=official?mod[c.name]:mod;result=fn(...args);}
 if(JSON.stringify(args)!==before)throw Error('input mutation');const outputs=new Set();identities(result,outputs,true);for(const obj of outputs)if(inputs.has(obj))throw Error('input output alias');
 if(c.id===894)result=result.map(encode);return result;
}
const cases=JSON.parse(fs.readFileSync(0,'utf8'));const output=cases.map(c=>{try{const result=invoke(c,false),wrapper=invoke(c,true);return {result,wrapper};}catch(e){return {error:e.stack};}});process.stdout.write(JSON.stringify(output));
