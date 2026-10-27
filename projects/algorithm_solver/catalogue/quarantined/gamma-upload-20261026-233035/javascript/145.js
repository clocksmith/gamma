'use strict';
// 145. Binary Tree Postorder Traversal.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
function solve(root) {
  const result = [];
  const stack = root === null ? [] : [[root, false]];
  while (stack.length) {
    const [node, ready] = stack.pop();
    if (ready) result.push(node.val);
    else {
      stack.push([node, true]);
      if (node.right !== null) stack.push([node.right, false]);
      if (node.left !== null) stack.push([node.left, false]);
    }
  }
  return result;
}
const postorderTraversal = solve;
class Solution { postorderTraversal(root) { return solve(root); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, postorderTraversal, TreeNode };
