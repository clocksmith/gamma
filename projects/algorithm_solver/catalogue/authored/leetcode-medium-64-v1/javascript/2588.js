'use strict';

// 2588. Count the Number of Beautiful Subarrays: count equal prefix XORs so every bit occurs an even number of times.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const counts = new Map([[0, 1]]);
  let prefix = 0;
  let answer = 0;
  for (const value of nums) {
    prefix ^= value;
    const previous = counts.get(prefix) || 0;
    answer += previous;
    counts.set(prefix, previous + 1);
  }
  return answer;
}

const beautifulSubarrays = solve;
class Solution {
  beautifulSubarrays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, beautifulSubarrays };
