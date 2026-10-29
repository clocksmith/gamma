"use strict";
function solve(root){const out=[],stack=root==null?[]:[root];while(stack.length){const n=stack.pop();out.push(n.val);const cs=n.children||[];for(let i=cs.length-1;i>=0;i--)stack.push(cs[i]);}return out;}

function preorder(root){return solve(root);}
module.exports=solve;
module.exports.preorder=preorder;
