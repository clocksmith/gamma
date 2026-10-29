"use strict";
function TreeNode(val=0,left=null,right=null) { this.val=val;this.left=left;this.right=right; }
function cloneTree(root) {
 if(root==null)return null;
 const result=new TreeNode(root.val),stack=[[root,result]];
 while(stack.length){const [old,copy]=stack.pop();for(const side of ['left','right'])if(old[side]!=null){copy[side]=new TreeNode(old[side].val);stack.push([old[side],copy[side]]);}}
 return result;
}
function solve(root,val){const result=cloneTree(root);if(result==null)return new TreeNode(val);let node=result;while(true){const side=val<node.val?'left':'right';if(node[side]==null){node[side]=new TreeNode(val);return result;}node=node[side];}}

function insertIntoBST(root, val){return solve(root, val);}
module.exports=solve;
module.exports.insertIntoBST=insertIntoBST;
module.exports.TreeNode=TreeNode;
