'use strict';

// 1679. Max Number of K-Sum Pairs: consume an unmatched complement before storing each value.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const unmatched = new Map();
  let pairs = 0;
  for (const value of nums) {
    const complement = k - value;
    const count = unmatched.get(complement) || 0;
    if (count > 0) {
      if (count === 1) unmatched.delete(complement);
      else unmatched.set(complement, count - 1);
      pairs += 1;
    } else {
      unmatched.set(value, (unmatched.get(value) || 0) + 1);
    }
  }
  return pairs;
}

const maxOperations = solve;
class Solution {
  maxOperations(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxOperations };
