'use strict';

// 2568. Minimum Impossible OR: find the first missing power of two since smaller powers generate every smaller value.
// O(n + log(M + 1)) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const present = new Set(nums);
  let value = 1;
  while (present.has(value)) value *= 2;
  return value;
}

const minImpossibleOR = solve;
class Solution {
  minImpossibleOR(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minImpossibleOR };
