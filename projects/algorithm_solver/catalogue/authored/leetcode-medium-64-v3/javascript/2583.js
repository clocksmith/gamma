'use strict';

// 2583. Kth Largest Sum in a Binary Tree: collect complete breadth-first level sums and select by descending order.
// O(n + l log l) time and O(n) auxiliary space for l levels; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root, k) {
  if (root === null) return -1;
  const sums = [];
  let frontier = [root];
  while (frontier.length) {
    let total = 0;
    const following = [];
    for (const node of frontier) {
      total += node.val;
      if (node.left !== null) following.push(node.left);
      if (node.right !== null) following.push(node.right);
    }
    sums.push(total);
    frontier = following;
  }
  if (k > sums.length) return -1;
  sums.sort((left, right) => right - left);
  return sums[k - 1];
}

const kthLargestLevelSum = solve;
class Solution {
  kthLargestLevelSum(root, k) { return solve(root, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthLargestLevelSum, TreeNode };
