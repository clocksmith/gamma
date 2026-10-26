'use strict';

// 3209. Number of Subarrays With AND Value of K.
// Merge the distinct AND values of suffixes ending at each index; O(n*B) time and O(B) space for B value bits. Inputs are preserved.

function solve(nums, k) {
  let suffixes = new Map(), answer = 0;
  for (const value of nums) {
    const current = new Map([[value, 1]]);
    for (const [previous, count] of suffixes) {
      const combined = previous & value;
      current.set(combined, (current.get(combined) || 0) + count);
    }
    answer += current.get(k) || 0;
    suffixes = current;
  }
  return answer;
}

const countSubarrays = solve;
class Solution {
  countSubarrays(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubarrays };
