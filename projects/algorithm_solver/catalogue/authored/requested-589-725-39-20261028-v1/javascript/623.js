"use strict";
function TreeNode(val=0,left=null,right=null) { this.val=val;this.left=left;this.right=right; }
function cloneTree(root) {
 if(root==null)return null;
 const result=new TreeNode(root.val),stack=[[root,result]];
 while(stack.length){const [old,copy]=stack.pop();for(const side of ['left','right'])if(old[side]!=null){copy[side]=new TreeNode(old[side].val);stack.push([old[side],copy[side]]);}}
 return result;
}
function solve(root,val,depth){const copy=cloneTree(root);if(depth===1)return new TreeNode(val,copy,null);let level=[copy];for(let d=1;d<depth-1;d++){const next=[];for(const n of level){if(n.left!=null)next.push(n.left);if(n.right!=null)next.push(n.right);}level=next;}for(const n of level){n.left=new TreeNode(val,n.left,null);n.right=new TreeNode(val,null,n.right);}return copy;}

function addOneRow(root, val, depth){return solve(root, val, depth);}
module.exports=solve;
module.exports.addOneRow=addOneRow;
module.exports.TreeNode=TreeNode;
