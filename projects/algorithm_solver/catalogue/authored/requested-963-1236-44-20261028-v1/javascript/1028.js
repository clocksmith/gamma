"use strict";
function TreeNode(val=0,left=null,right=null) { this.val=val;this.left=left;this.right=right; }
function cloneTree(root) {
 if(root==null)return null;
 const result=new TreeNode(root.val),stack=[[root,result]];
 while(stack.length){const [old,copy]=stack.pop();for(const side of ['left','right'])if(old[side]!=null){copy[side]=new TreeNode(old[side].val);stack.push([old[side],copy[side]]);}}
 return result;
}
function solve(traversal){const stack=[];let at=0;while(at<traversal.length){let depth=0;while(traversal[at]==='-'){depth++;at++;}let end=at;while(end<traversal.length&&traversal[end]>='0'&&traversal[end]<='9')end++;const n=new TreeNode(Number(traversal.slice(at,end)));at=end;while(stack.length>depth)stack.pop();if(stack.length){const p=stack[stack.length-1];if(p.left==null)p.left=n;else p.right=n;}stack.push(n);}return stack[0];}

function recoverFromPreorder(traversal){return solve(traversal);}
module.exports=solve;
module.exports.recoverFromPreorder=recoverFromPreorder;
module.exports.TreeNode=TreeNode;
