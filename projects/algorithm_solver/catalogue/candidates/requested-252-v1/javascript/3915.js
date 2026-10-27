'use strict';

// 3915. Maximum Sum of Alternating Subsequence With Distance at Least K.
// Specification: https://leetcode.com/problems/maximum-sum-of-alternating-subsequence-with-distance-at-least-k/description/
// O(n log n) time, O(n) space; activate only predecessors at distance at least k. Inputs are preserved.
function solve(nums, k) {
  const values = [...new Set(nums)].sort((a, b) => a - b);
  const ranks = new Map(values.map((value, index) => [value, index + 1]));
  const size = values.length;
  const lower = new Array(size + 1).fill(0), upper = new Array(size + 1).fill(0);
  const up = new Array(nums.length), down = new Array(nums.length);
  function update(tree, index, value) {
    for (; index <= size; index += index & -index) tree[index] = Math.max(tree[index], value);
  }
  function prefix(tree, index) {
    let value = 0;
    for (; index; index -= index & -index) value = Math.max(value, tree[index]);
    return value;
  }
  let answer = 0;
  for (let index = 0; index < nums.length; index++) {
    if (index >= k) {
      const previous = index - k, rank = ranks.get(nums[previous]);
      update(lower, rank, down[previous]);
      update(upper, size - rank + 1, up[previous]);
    }
    const rank = ranks.get(nums[index]);
    up[index] = nums[index] + prefix(lower, rank - 1);
    down[index] = nums[index] + prefix(upper, size - rank);
    answer = Math.max(answer, up[index], down[index]);
  }
  return answer;
}

// Native judge method name is not established; canonical solve is the supported entry point.
if (typeof module !== 'undefined') module.exports = { solve };
