"use strict";
function TreeNode(val=0,left=null,right=null) { this.val=val;this.left=left;this.right=right; }
function cloneTree(root) {
 if(root==null)return null;
 const result=new TreeNode(root.val),stack=[[root,result]];
 while(stack.length){const [old,copy]=stack.pop();for(const side of ['left','right'])if(old[side]!=null){copy[side]=new TreeNode(old[side].val);stack.push([old[side],copy[side]]);}}
 return result;
}
function solve(nums){const stack=[];for(const value of nums){const node=new TreeNode(value);while(stack.length&&stack[stack.length-1].val<value)node.left=stack.pop();if(stack.length)stack[stack.length-1].right=node;stack.push(node);}return stack[0];}

function constructMaximumBinaryTree(nums){return solve(nums);}
module.exports=solve;
module.exports.constructMaximumBinaryTree=constructMaximumBinaryTree;
module.exports.TreeNode=TreeNode;
