'use strict';

// 3760. Maximum Substrings With Distinct Start.
// O(n) time and O(26) space; cut at the first occurrence of each new starting letter.
function solve(s) {
  return new Set(s).size;
}

const maxDistinct = solve;
class Solution {
  maxDistinct(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDistinct };
