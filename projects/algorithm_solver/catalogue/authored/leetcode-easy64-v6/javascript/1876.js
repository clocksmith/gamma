'use strict';

// 1876. Substrings of Size Three with Distinct Characters (Easy).
// Specification: https://leetcode.com/problems/substrings-of-size-three-with-distinct-characters/description/
// O(n) time, O(1) space; count each length-three occurrence independently.
function solve(s) {
  let result = 0;
  for (let index = 2; index < s.length; index++) {
    if (s[index - 2] !== s[index - 1] && s[index - 2] !== s[index] && s[index - 1] !== s[index]) result++;
  }
  return result;
}

const countGoodSubstrings = solve;
class Solution {
  countGoodSubstrings(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countGoodSubstrings };
