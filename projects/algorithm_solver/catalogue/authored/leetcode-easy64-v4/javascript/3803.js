'use strict';

// 3803. Count Residue Prefixes (Easy).
// Specification: https://leetcode.com/problems/count-residue-prefixes/description/
// O(n) time, O(1) lowercase alphabet space; count nonempty prefixes.
function solve(s) {
  const seen = new Array(26).fill(false);
  let distinct = 0;
  let result = 0;
  for (let index = 0; index < s.length; index++) {
    const letter = s.charCodeAt(index) - 97;
    if (!seen[letter]) {
      seen[letter] = true;
      distinct++;
    }
    if (distinct === (index + 1) % 3) result++;
  }
  return result;
}

const residuePrefixes = solve;
class Solution {
  residuePrefixes(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, residuePrefixes };
