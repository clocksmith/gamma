'use strict';

// 2236. Root Equals Sum of Children (Easy).
// Specification: https://leetcode.com/problems/root-equals-sum-of-children/description/
// O(1) time and space; the problem supplies exactly a root and two children.
function solve(root) {
  return root.val === root.left.val + root.right.val;
}

const checkTree = solve;
class Solution {
  checkTree(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkTree };
