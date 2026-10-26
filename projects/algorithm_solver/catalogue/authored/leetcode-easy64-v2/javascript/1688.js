'use strict';

// 1688. Count of Matches in Tournament (Easy).
// Specification: https://leetcode.com/problems/count-of-matches-in-tournament/description/
// O(1) time and space; every match eliminates exactly one of n teams.
function solve(n) {
  return n - 1;
}

const numberOfMatches = solve;
class Solution {
  numberOfMatches(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfMatches };
