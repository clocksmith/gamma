'use strict';

// 2331. Evaluate Boolean Binary Tree (Easy).
// Specification: https://leetcode.com/problems/evaluate-boolean-binary-tree/description/
// O(n) time, O(h) auxiliary space; iterative postorder on supplied val/left/right nodes; no tree mutation.
function solve(root) {
  const pending = [[root, false]];
  const values = [];
  while (pending.length > 0) {
    const [node, expanded] = pending.pop();
    if (node.val === 0 || node.val === 1) {
      values.push(node.val === 1);
    } else if (expanded) {
      const right = values.pop();
      const left = values.pop();
      values.push(node.val === 2 ? left || right : left && right);
    } else {
      pending.push([node, true]);
      pending.push([node.right, false]);
      pending.push([node.left, false]);
    }
  }
  return values[0];
}

const evaluateTree = solve;
class Solution {
  evaluateTree(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, evaluateTree };
