"use strict";
function TreeNode(val=0,left=null,right=null) { this.val=val;this.left=left;this.right=right; }
function cloneTree(root) {
 if(root==null)return null;
 const result=new TreeNode(root.val),stack=[[root,result]];
 while(stack.length){const [old,copy]=stack.pop();for(const side of ['left','right'])if(old[side]!=null){copy[side]=new TreeNode(old[side].val);stack.push([old[side],copy[side]]);}}
 return result;
}
function solve(root){const out=cloneTree(root),stack=[];let node=out,total=0;while(node!=null||stack.length){while(node!=null){stack.push(node);node=node.right;}node=stack.pop();total+=node.val;node.val=total;node=node.left;}return out;}

function bstToGst(root){return solve(root);}
module.exports=solve;
module.exports.bstToGst=bstToGst;
module.exports.TreeNode=TreeNode;
