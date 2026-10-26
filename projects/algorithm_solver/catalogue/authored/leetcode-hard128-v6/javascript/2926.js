'use strict';

// 2926. Maximum Balanced Subsequence Sum.
// Fenwick maximum over compressed value-minus-index keys; O(n log n) time, O(n) space. Inputs are preserved.

function solve(nums) {
  const keys = [...new Set(nums.map((value, index) => value - index))].sort((a, b) => a - b);
  const ranks = new Map(keys.map((value, index) => [value, index + 1])), tree = Array(keys.length + 1).fill(0);
  let answer = -Infinity;
  for (let position = 0; position < nums.length; position += 1) {
    const rank = ranks.get(nums[position] - position);
    let previous = 0;
    for (let i = rank; i > 0; i -= i & -i) previous = Math.max(previous, tree[i]);
    const current = previous + nums[position];
    answer = Math.max(answer, current);
    for (let i = rank; i < tree.length; i += i & -i) tree[i] = Math.max(tree[i], current);
  }
  return answer;
}

const maxBalancedSubsequenceSum = solve;
class Solution {
  maxBalancedSubsequenceSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxBalancedSubsequenceSum };
