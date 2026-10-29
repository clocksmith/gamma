"use strict";
function solve(root){const out=[],stack=[root];while(stack.length){const x=stack.pop();if(typeof x==='string'){out.push(x);continue;}out.push(String(x.val));if(x.right!=null)stack.push(')',x.right,'(');if(x.left!=null||x.right!=null){stack.push(')');if(x.left!=null)stack.push(x.left);stack.push('(');}}return out.join('');}

function tree2str(root){return solve(root);}
module.exports=solve;
module.exports.tree2str=tree2str;
