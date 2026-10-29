"use strict";
function TreeNode(val=0,left=null,right=null) { this.val=val;this.left=left;this.right=right; }
function cloneTree(root) {
 if(root==null)return null;
 const result=new TreeNode(root.val),stack=[[root,result]];
 while(stack.length){const [old,copy]=stack.pop();for(const side of ['left','right'])if(old[side]!=null){copy[side]=new TreeNode(old[side].val);stack.push([old[side],copy[side]]);}}
 return result;
}
function solve(root,to_delete){const copy=cloneTree(root),deleted=new Set(to_delete),out=[],stack=[[copy,null,null]];while(stack.length){const [n,parent,side]=stack.pop(),remove=deleted.has(n.val);if(remove){if(parent!=null)parent[side]=null;}else if(parent==null)out.push(n);for(const label of ['left','right'])if(n[label]!=null)stack.push([n[label],remove?null:n,label]);}return out;}

function delNodes(root, to_delete){return solve(root, to_delete);}
module.exports=solve;
module.exports.delNodes=delNodes;
module.exports.TreeNode=TreeNode;
