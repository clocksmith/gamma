'use strict';

// 2598. Smallest Missing Non-negative Integer After Operations: consume available residue classes in increasing target order.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums, value) {
  const counts = new Map();
  for (const number of nums) {
    const remainder = ((number % value) + value) % value;
    counts.set(remainder, (counts.get(remainder) || 0) + 1);
  }
  let result = 0;
  while ((counts.get(result % value) || 0) > 0) {
    const remainder = result % value;
    counts.set(remainder, counts.get(remainder) - 1);
    result += 1;
  }
  return result;
}

const findSmallestInteger = solve;
class Solution {
  findSmallestInteger(nums, value) { return solve(nums, value); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findSmallestInteger };
