'use strict';

// 2779. Maximum Beauty of an Array After Applying Operation: find the largest sorted window whose value range is at most twice k.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const ordered = nums.slice().sort((left, right) => left - right);
  let left = 0;
  let best = 0;
  for (let right = 0; right < ordered.length; right += 1) {
    while (ordered[right] - ordered[left] > 2 * k) left += 1;
    best = Math.max(best, right - left + 1);
  }
  return best;
}

const maximumBeauty = solve;
class Solution {
  maximumBeauty(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumBeauty };
