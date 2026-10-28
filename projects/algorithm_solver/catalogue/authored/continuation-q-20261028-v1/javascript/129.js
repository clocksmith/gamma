"use strict";
class TreeNode {constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
function solve(root) {
if(root===null)return 0;const pending=[[root,0]];let total=0;while(pending.length){const [node,prefix]=pending.pop(),value=prefix*10+node.val;if(node.left===null&&node.right===null)total+=value;else{if(node.right!==null)pending.push([node.right,value]);if(node.left!==null)pending.push([node.left,value]);}}return total;
}
function sumNumbers(root) { return solve(root); }
class Solution {sumNumbers(root) { return solve(root); }}
module.exports=solve;
module.exports.sumNumbers=sumNumbers;
module.exports.Solution=Solution;
module.exports.TreeNode=TreeNode;
