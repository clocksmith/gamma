'use strict';

// 3438. Find Valid Pair of Adjacent Digits in String (Easy).
// Specification: https://leetcode.com/problems/find-valid-pair-of-adjacent-digits-in-string/description/
// O(n) time, O(1) digit space; return the first qualifying adjacent pair.
function solve(s) {
  const counts = new Array(10).fill(0);
  for (const character of s) counts[character.charCodeAt(0) - 48]++;
  for (let index = 0; index + 1 < s.length; index++) {
    const first = s.charCodeAt(index) - 48;
    const second = s.charCodeAt(index + 1) - 48;
    if (first !== second && counts[first] === first && counts[second] === second) {
      return s.slice(index, index + 2);
    }
  }
  return '';
}

const findValidPair = solve;
class Solution {
  findValidPair(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findValidPair };
