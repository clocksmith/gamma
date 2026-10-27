'use strict';

// 663. Equal Tree Partition.

function solve(root) {
  if (root === null) return false;
  const sums = new Map(), proper = new Set(), stack = [[root, false]];
  while (stack.length > 0) {
    const [node, ready] = stack.pop();
    if (!ready) {
      stack.push([node, true]); if (node.right) stack.push([node.right, false]); if (node.left) stack.push([node.left, false]);
    } else {
      const total = node.val + (sums.get(node.left) || 0) + (sums.get(node.right) || 0);
      sums.set(node, total); if (node !== root) proper.add(total);
    }
  }
  const total = sums.get(root);
  return total % 2 === 0 && proper.has(total / 2);
}

const checkEqualTree = solve;
class Solution {
  checkEqualTree(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkEqualTree };
