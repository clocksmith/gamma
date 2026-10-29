"use strict";
function TreeNode(val=0,left=null,right=null) { this.val=val;this.left=left;this.right=right; }
function cloneTree(root) {
 if(root==null)return null;
 const result=new TreeNode(root.val),stack=[[root,result]];
 while(stack.length){const [old,copy]=stack.pop();for(const side of ['left','right'])if(old[side]!=null){copy[side]=new TreeNode(old[side].val);stack.push([old[side],copy[side]]);}}
 return result;
}
function solve(root1,root2){if(root1==null&&root2==null)return null;const result=new TreeNode(),stack=[[root1,root2,result]];while(stack.length){const [a,b,out]=stack.pop();out.val=(a?.val??0)+(b?.val??0);for(const side of ['left','right']){const x=a?.[side]??null,y=b?.[side]??null;if(x!=null||y!=null){out[side]=new TreeNode();stack.push([x,y,out[side]]);}}}return result;}

function mergeTrees(root1, root2){return solve(root1, root2);}
module.exports=solve;
module.exports.mergeTrees=mergeTrees;
module.exports.TreeNode=TreeNode;
