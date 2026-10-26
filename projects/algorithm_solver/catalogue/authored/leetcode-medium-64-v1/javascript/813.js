'use strict';

// 813. Largest Sum of Averages: partition positive prefixes with rolling dynamic programming.
// O(k * n^2) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const size = nums.length;
  const prefix = new Array(size + 1).fill(0);
  for (let index = 0; index < size; index += 1) prefix[index + 1] = prefix[index] + nums[index];
  let previous = new Array(size + 1).fill(0);
  for (let end = 1; end <= size; end += 1) previous[end] = prefix[end] / end;
  // Positive values make an optimal partition use all k available groups.
  for (let groups = 2; groups <= k; groups += 1) {
    const current = new Array(size + 1).fill(-Infinity);
    for (let end = groups; end <= size; end += 1) {
      for (let split = groups - 1; split < end; split += 1) {
        const candidate = previous[split] + (prefix[end] - prefix[split]) / (end - split);
        current[end] = Math.max(current[end], candidate);
      }
    }
    previous = current;
  }
  return previous[size];
}

const largestSumOfAverages = solve;
class Solution {
  largestSumOfAverages(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestSumOfAverages };
