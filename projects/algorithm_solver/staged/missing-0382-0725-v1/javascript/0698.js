'use strict';

// 698. Partition to K Equal Sum Subsets. Subset-mask DP records the unfinished bucket sum; O(n*2^n) time.

function solve(nums, k) {
  const total = nums.reduce((sum, value) => sum + value, 0);
  if (k > nums.length || total % k !== 0) return false;
  const target = total / k;
  if (target === 0) return true;
  const ordered = nums.slice().sort((a, b) => a - b);
  if (ordered[ordered.length - 1] > target) return false;
  const size = 1 << nums.length, remainder = Array(size).fill(-1);
  remainder[0] = 0;
  for (let mask = 0; mask < size; mask += 1) {
    if (remainder[mask] < 0) continue;
    for (let i = 0; i < ordered.length; i += 1) {
      if ((mask & (1 << i)) !== 0) continue;
      if (remainder[mask] + ordered[i] > target) break;
      remainder[mask | (1 << i)] = (remainder[mask] + ordered[i]) % target;
    }
  }
  return remainder[size - 1] === 0;
}

const canPartitionKSubsets = solve;
class Solution {
  canPartitionKSubsets(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canPartitionKSubsets };
