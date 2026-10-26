'use strict';

// 2527. Find Xor-Beauty of Array: cancel the repeated triple contributions independently at each bit.
// O(n) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(nums) {
  let result = 0;
  for (const value of nums) result ^= value;
  return result;
}

const xorBeauty = solve;
class Solution {
  xorBeauty(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, xorBeauty };
