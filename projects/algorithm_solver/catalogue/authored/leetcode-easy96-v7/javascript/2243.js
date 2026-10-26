'use strict';

// 2243. Calculate Digit Sum of a String (Easy).
// Specification: https://leetcode.com/problems/calculate-digit-sum-of-a-string/description/
// O(n) total time and O(n) space for k >= 2; sum consecutive groups until at most k digits remain.
function solve(s, k) {
  let current = s;
  while (current.length > k) {
    const groups = [];
    for (let start = 0; start < current.length; start += k) {
      let total = 0;
      const end = Math.min(start + k, current.length);
      for (let index = start; index < end; index++) total += current.charCodeAt(index) - 48;
      groups.push(String(total));
    }
    current = groups.join('');
  }
  return current;
}

const digitSum = solve;
class Solution {
  digitSum(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, digitSum };
