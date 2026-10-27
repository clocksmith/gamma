'use strict';
// 108. Convert Sorted Array to Binary Search Tree.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
function solve(nums) {
  function build(left, right) {
    if (left >= right) return null;
    const middle = Math.floor((left + right) / 2);
    return new TreeNode(nums[middle], build(left, middle), build(middle + 1, right));
  }
  return build(0, nums.length);
}
const sortedArrayToBST = solve;
class Solution { sortedArrayToBST(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortedArrayToBST, TreeNode };
