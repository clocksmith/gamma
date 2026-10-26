'use strict';

// 1373. Maximum Sum BST in Binary Tree.
// Iterative postorder stores validity, extrema and sum for each subtree; O(n) time and space. The input tree is preserved.

function solve(root) {
  if (root == null) return 0;
  const info = new Map();
  const empty = [true, Infinity, -Infinity, 0];
  const stack = [[root, false]];
  let answer = 0;
  while (stack.length > 0) {
    const [node, finished] = stack.pop();
    if (!finished) {
      stack.push([node, true]);
      if (node.right != null) stack.push([node.right, false]);
      if (node.left != null) stack.push([node.left, false]);
      continue;
    }
    const left = info.get(node.left) || empty;
    const right = info.get(node.right) || empty;
    info.delete(node.left);
    info.delete(node.right);
    if (left[0] && right[0] && left[2] < node.val && node.val < right[1]) {
      const total = left[3] + right[3] + node.val;
      answer = Math.max(answer, total);
      info.set(node, [true, Math.min(left[1], node.val), Math.max(right[2], node.val), total]);
    } else info.set(node, [false, 0, 0, 0]);
  }
  return answer;
}

const maxSumBST = solve;
class Solution {
  maxSumBST(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSumBST };
