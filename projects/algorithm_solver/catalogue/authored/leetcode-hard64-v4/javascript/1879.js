'use strict';

// 1879. Minimum XOR Sum of Two Arrays. Assignment DP over used positions; O(n*2^n) time and O(2^n) space. Inputs are preserved.

function solve(nums1, nums2) {
  const size = nums1.length;
  const count = 1 << size;
  const best = Array(count).fill(Infinity);
  const used = new Uint8Array(count);
  best[0] = 0;
  for (let mask = 1; mask < count; mask += 1) used[mask] = used[mask >>> 1] + (mask & 1);
  for (let mask = 0; mask < count - 1; mask += 1) {
    const index = used[mask];
    for (let other = 0; other < size; other += 1) {
      const bit = 1 << other;
      if ((mask & bit) === 0) {
        const following = mask | bit;
        best[following] = Math.min(best[following], best[mask] + (nums1[index] ^ nums2[other]));
      }
    }
  }
  return best[count - 1];
}

const minimumXORSum = solve;
class Solution {
  minimumXORSum(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumXORSum };
