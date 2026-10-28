'use strict';

// 338. Counting Bits (Easy).
// Specification: https://leetcode.com/problems/counting-bits/description/
function solve(n) {
  const answer = new Array(n + 1).fill(0);
  for (let value = 1; value <= n; value++) answer[value] = answer[value >> 1] + (value & 1);
  return answer;
}

const countBits = solve;
class Solution {
  countBits(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countBits };
