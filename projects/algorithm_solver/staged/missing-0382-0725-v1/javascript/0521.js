'use strict';

// 521. Longest Uncommon Subsequence I.

function solve(a, b) {
  return a === b ? -1 : Math.max(a.length, b.length);
}

const findLUSlength = solve;
class Solution {
  findLUSlength(a, b) { return solve(a, b); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLUSlength };
