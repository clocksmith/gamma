"use strict";
function solve(root){const out=[],stack=root==null?[]:[root];while(stack.length){const n=stack.pop();out.push(n.val);for(const c of n.children||[])stack.push(c);}out.reverse();return out;}

function postorder(root){return solve(root);}
module.exports=solve;
module.exports.postorder=postorder;
