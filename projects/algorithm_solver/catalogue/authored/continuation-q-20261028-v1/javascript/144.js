"use strict";
class TreeNode {constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
function solve(root) {
const answer=[],pending=root===null?[]:[root];while(pending.length){const node=pending.pop();answer.push(node.val);if(node.right!==null)pending.push(node.right);if(node.left!==null)pending.push(node.left);}return answer;
}
function preorderTraversal(root) { return solve(root); }
class Solution {preorderTraversal(root) { return solve(root); }}
module.exports=solve;
module.exports.preorderTraversal=preorderTraversal;
module.exports.Solution=Solution;
module.exports.TreeNode=TreeNode;
