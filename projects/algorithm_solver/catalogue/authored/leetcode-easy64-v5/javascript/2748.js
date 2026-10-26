'use strict';

// 2748. Number of Beautiful Pairs (Easy).
// Specification: https://leetcode.com/problems/number-of-beautiful-pairs/description/
// O(n * d) time, O(1) auxiliary space; d is maximum decimal digit count; preserve nums.
function solve(nums) {
  function gcd(left, right) {
    while (right !== 0) {
      const remainder = left % right;
      left = right;
      right = remainder;
    }
    return left;
  }
  const firstDigits = new Array(10).fill(0);
  let pairs = 0;
  for (const value of nums) {
    const lastDigit = value % 10;
    for (let digit = 1; digit <= 9; digit++) {
      if (gcd(digit, lastDigit) === 1) pairs += firstDigits[digit];
    }
    let firstDigit = value;
    while (firstDigit >= 10) firstDigit = Math.floor(firstDigit / 10);
    firstDigits[firstDigit]++;
  }
  return pairs;
}

const countBeautifulPairs = solve;
class Solution {
  countBeautifulPairs(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countBeautifulPairs };
