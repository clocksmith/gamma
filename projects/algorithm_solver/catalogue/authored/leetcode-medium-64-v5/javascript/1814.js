'use strict';

// 1814. Count Nice Pairs in an Array: group values by their difference from their digit reversal.
// O(n * log(M + 1)) expected time and O(n) space, with M the largest value; inputs are read-only.
function solve(nums) {
  const modulus = 1000000007;
  const counts = new Map();
  let result = 0;
  for (const value of nums) {
    let remaining = value;
    let reversedValue = 0;
    while (remaining > 0) {
      reversedValue = reversedValue * 10 + remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
    const key = value - reversedValue;
    const previous = counts.get(key) || 0;
    result = (result + previous) % modulus;
    counts.set(key, previous + 1);
  }
  return result;
}

const countNicePairs = solve;
class Solution {
  countNicePairs(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countNicePairs };
