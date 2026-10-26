'use strict';

// 1818. Minimum Absolute Sum Difference: find the best single replacement by binary searching a sorted copy.
// O(n * log(n + 1)) time and O(n) auxiliary space; inputs are read-only.
function solve(nums1, nums2) {
  const ordered = nums1.slice().sort((a, b) => a - b);
  let total = 0;
  let improvement = 0;
  for (let index = 0; index < nums1.length; index += 1) {
    const target = nums2[index];
    const difference = Math.abs(nums1[index] - target);
    total += difference;
    let low = 0;
    let high = ordered.length;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (ordered[middle] < target) low = middle + 1;
      else high = middle;
    }
    let nearest = difference;
    if (low < ordered.length) nearest = Math.min(nearest, ordered[low] - target);
    if (low > 0) nearest = Math.min(nearest, target - ordered[low - 1]);
    improvement = Math.max(improvement, difference - nearest);
  }
  return (total - improvement) % 1000000007;
}

const minAbsoluteSumDiff = solve;
class Solution {
  minAbsoluteSumDiff(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minAbsoluteSumDiff };
