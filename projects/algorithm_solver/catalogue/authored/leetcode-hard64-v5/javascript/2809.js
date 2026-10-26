'use strict';

// 2809. Minimum Time to Make Array Sum At Most x. Order resets by growth and maximize saved value for each reset count; O(n^2) time and O(n) space. Inputs are preserved.

function solve(nums1, nums2, x) {
  const size = nums1.length;
  const ordered = nums1.map((initial, index) => [nums2[index], initial]).sort((a, b) => a[0] - b[0]);
  const saved = Array(size + 1).fill(-Infinity);
  saved[0] = 0;
  for (let index = 0; index < size; index += 1) {
    const [growth, initial] = ordered[index];
    for (let resets = index + 1; resets > 0; resets -= 1) saved[resets] = Math.max(saved[resets], saved[resets - 1] + initial + growth * resets);
  }
  let initialSum = 0;
  let growthSum = 0;
  for (let index = 0; index < size; index += 1) { initialSum += nums1[index]; growthSum += nums2[index]; }
  for (let elapsed = 0; elapsed <= size; elapsed += 1) {
    if (initialSum + elapsed * growthSum - saved[elapsed] <= x) return elapsed;
  }
  return -1;
}

const minimumTime = solve;
class Solution {
  minimumTime(nums1, nums2, x) { return solve(nums1, nums2, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTime };
