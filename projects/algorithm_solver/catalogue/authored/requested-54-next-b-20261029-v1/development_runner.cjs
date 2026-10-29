"use strict";
const fs=require('fs'),path=require('path'),root=process.argv[2];
class TreeNode{constructor(val,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
function tree(values){const root=new TreeNode(values[0]),q=[root];let index=1;for(let h=0;h<q.length;h++)for(const side of ['left','right']){if(index>=values.length)break;const v=values[index++];if(v!==null){q[h][side]=new TreeNode(v);q.push(q[h][side]);}}return root;}
function invoke(c,official){const mod=require(path.join(root,'javascript',c.id+'.js')),args=JSON.parse(JSON.stringify(c.args));if(c.id===863)args[0]=tree(args[0]);const before=JSON.stringify(args);let result;
 if([855,900,901].includes(c.id)){const [ops,rows]=args,receiver=new mod[ops[0]](...rows[0]);result=[null];for(let i=1;i<ops.length;i++){const value=receiver[ops[i]](...rows[i]);if(ops[i]==='leave'&&value!==undefined)throw Error('void contract');result.push(value===undefined?null:value);}}
 else{const fn=official?mod[c.id===863?'distanceK':'superEggDrop']:mod;result=fn(...args);}
 if(JSON.stringify(args)!==before)throw Error('input mutation');if(c.id===863&&result===args[0])throw Error('output alias');return result;
}
process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(c=>{try{return {result:invoke(c,false),official:invoke(c,true)};}catch(e){return {error:e.stack};}})));
