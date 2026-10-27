'use strict';
// 101. Symmetric Tree.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
function solve(root) {
  if (root === null) return true;
  const queue = [[root.left, root.right]];
  for (let head = 0; head < queue.length; head += 1) {
    const [left, right] = queue[head];
    if (left === null || right === null) {
      if (left !== right) return false;
      continue;
    }
    if (left.val !== right.val) return false;
    queue.push([left.left, right.right], [left.right, right.left]);
  }
  return true;
}
const isSymmetric = solve;
class Solution { isSymmetric(root) { return solve(root); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isSymmetric, TreeNode };
