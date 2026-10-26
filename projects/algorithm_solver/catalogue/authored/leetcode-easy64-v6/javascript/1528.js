'use strict';

// 1528. Shuffle String (Easy).
// Specification: https://leetcode.com/problems/shuffle-string/description/
// O(n) time and space; preserve indices.
function solve(s, indices) {
  const result = new Array(s.length);
  for (let index = 0; index < s.length; index++) result[indices[index]] = s[index];
  return result.join('');
}

const restoreString = solve;
class Solution {
  restoreString(s, indices) { return solve(s, indices); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, restoreString };
