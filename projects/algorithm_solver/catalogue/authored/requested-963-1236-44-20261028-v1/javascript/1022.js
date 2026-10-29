"use strict";
function solve(root){const stack=[[root,0]];let answer=0;while(stack.length){const [n,previous]=stack.pop(),value=previous*2+n.val;if(n.left==null&&n.right==null)answer+=value;if(n.left!=null)stack.push([n.left,value]);if(n.right!=null)stack.push([n.right,value]);}return answer;}

function sumRootToLeaf(root){return solve(root);}
module.exports=solve;
module.exports.sumRootToLeaf=sumRootToLeaf;
