'use strict';

// 938. Range Sum of BST (Easy).
// Specification: https://leetcode.com/problems/range-sum-of-bst/description/
// O(n) worst-case time, O(h) auxiliary space; preserve the supplied tree.
function solve(root, low, high) {
  const stack = [root];
  let total = 0;
  while (stack.length > 0) {
    const node = stack.pop();
    if (node === null) continue;
    if (low <= node.val && node.val <= high) total += node.val;
    if (node.val > low && node.left !== null) stack.push(node.left);
    if (node.val < high && node.right !== null) stack.push(node.right);
  }
  return total;
}

const rangeSumBST = solve;
class Solution {
  rangeSumBST(root, low, high) { return solve(root, low, high); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rangeSumBST };
