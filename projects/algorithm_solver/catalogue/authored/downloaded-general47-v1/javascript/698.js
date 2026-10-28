'use strict';

// 698. Partition to K Equal Sum Subsets (Medium).
// Specification: https://leetcode.com/problems/partition-to-k-equal-sum-subsets/description/
function solve(nums, k) {
  const total = nums.reduce((sum, value) => sum + value, 0);
  if (total % k !== 0) return false;
  const target = total / k;
  const sorted = nums.slice().sort((a, b) => b - a);
  if (sorted[0] > target) return false;
  const buckets = new Array(k).fill(0);
  function backtrack(index) {
    if (index === sorted.length) return buckets.every((value) => value === target);
    for (let i = 0; i < k; i++) {
      if (buckets[i] + sorted[index] > target) continue;
      if (i > 0 && buckets[i] === buckets[i - 1]) continue;
      buckets[i] += sorted[index];
      if (backtrack(index + 1)) return true;
      buckets[i] -= sorted[index];
    }
    return false;
  }
  return backtrack(0);
}
const canPartitionKSubsets = solve;
class Solution { canPartitionKSubsets(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canPartitionKSubsets };
