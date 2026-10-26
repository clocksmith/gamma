'use strict';

// 3724. Minimum Operations to Transform Array.
// O(n) time and O(1) auxiliary space; copy once from the closest required adjustment interval.
function solve(nums1, nums2) {
  const target = nums2[nums2.length - 1];
  let extra = Infinity;
  let answer = 1;
  for (let index = 0; index < nums1.length; index += 1) {
    const source = nums1[index];
    const destination = nums2[index];
    answer += Math.abs(source - destination);
    const low = Math.min(source, destination);
    const high = Math.max(source, destination);
    extra = Math.min(extra, Math.max(low - target, target - high, 0));
  }
  return answer + extra;
}

const minOperations = solve;
class Solution {
  minOperations(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
