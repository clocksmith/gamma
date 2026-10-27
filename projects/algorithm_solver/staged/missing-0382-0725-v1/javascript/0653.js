'use strict';

// 653. Two Sum IV - Input is a BST.

function solve(root, k) {
  const seen = new Set(), stack = root ? [root] : [];
  while (stack.length > 0) {
    const node = stack.pop();
    if (seen.has(k - node.val)) return true;
    seen.add(node.val);
    if (node.right) stack.push(node.right); if (node.left) stack.push(node.left);
  }
  return false;
}

const findTarget = solve;
class Solution {
  findTarget(root, k) { return solve(root, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findTarget };
