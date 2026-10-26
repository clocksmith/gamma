'use strict';

// 3827. Count Monobit Integers (Easy).
// Specification: https://leetcode.com/problems/count-monobit-integers/description/
// O(log(n + 2)) time, O(1) space; include zero and all-ones binary representations.
function solve(n) {
  let result = 1;
  let value = 1;
  while (value <= n) {
    result++;
    value = value * 2 + 1;
  }
  return result;
}

const countMonobit = solve;
class Solution {
  countMonobit(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countMonobit };
