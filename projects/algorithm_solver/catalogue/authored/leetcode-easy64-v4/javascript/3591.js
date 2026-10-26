'use strict';

// 3591. Check if Any Element Has Prime Frequency (Easy).
// Specification: https://leetcode.com/problems/check-if-any-element-has-prime-frequency/description/
// O(n + u * sqrt(n)) time, O(u) space; u is the distinct-value count; preserve nums.
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  for (const count of counts.values()) {
    if (count < 2) continue;
    let prime = true;
    for (let divisor = 2; divisor * divisor <= count; divisor++) {
      if (count % divisor === 0) {
        prime = false;
        break;
      }
    }
    if (prime) return true;
  }
  return false;
}

const checkPrimeFrequency = solve;
class Solution {
  checkPrimeFrequency(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkPrimeFrequency };
