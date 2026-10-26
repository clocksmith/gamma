'use strict';

// 507. Perfect Number (Easy).
// Specification: https://leetcode.com/problems/perfect-number/description/
// O(sqrt(num)) time, O(1) space; count each proper-divisor pair once.
function solve(num) {
  if (num <= 1) return false;
  let total = 1;
  for (let divisor = 2; divisor * divisor <= num; divisor++) {
    if (num % divisor !== 0) continue;
    total += divisor;
    const partner = num / divisor;
    if (partner !== divisor) total += partner;
  }
  return total === num;
}

const checkPerfectNumber = solve;
class Solution {
  checkPerfectNumber(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkPerfectNumber };
