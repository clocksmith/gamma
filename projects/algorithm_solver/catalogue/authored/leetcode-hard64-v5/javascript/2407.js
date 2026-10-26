'use strict';

// 2407. Longest Increasing Subsequence II. Range-maximum segment tree over preceding values; O(M+n log M) time and O(M) space, M=max(nums)+1. Inputs are preserved.

function solve(nums, k) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  let size = 1;
  while (size <= maximum) size *= 2;
  const tree = Array(2 * size).fill(0);
  let answer = 0;
  for (const value of nums) {
    let left = size + Math.max(0, value - k);
    let right = size + value;
    let previous = 0;
    while (left < right) {
      if (left % 2 === 1) previous = Math.max(previous, tree[left++]);
      if (right % 2 === 1) previous = Math.max(previous, tree[--right]);
      left = Math.floor(left / 2);
      right = Math.floor(right / 2);
    }
    const current = previous + 1;
    let node = size + value;
    tree[node] = Math.max(tree[node], current);
    for (node = Math.floor(node / 2); node > 0; node = Math.floor(node / 2)) {
      tree[node] = Math.max(tree[2 * node], tree[2 * node + 1]);
    }
    answer = Math.max(answer, current);
  }
  return answer;
}

const lengthOfLIS = solve;
class Solution {
  lengthOfLIS(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lengthOfLIS };
