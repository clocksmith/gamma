"use strict";
function solve(root,k){const seen=new Set(),stack=[root];while(stack.length){const n=stack.pop();if(seen.has(k-n.val))return true;seen.add(n.val);if(n.left!=null)stack.push(n.left);if(n.right!=null)stack.push(n.right);}return false;}

function findTarget(root, k){return solve(root, k);}
module.exports=solve;
module.exports.findTarget=findTarget;
