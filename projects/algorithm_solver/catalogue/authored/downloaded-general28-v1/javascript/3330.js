'use strict';

// 3330. Find the Original Typed String I (Easy).
// Specification: https://leetcode.com/problems/find-the-original-typed-string-i/description/
function solve(word) {
  let ans = 1;
  for (let i = 1; i < word.length; i++) if (word[i] === word[i - 1]) ans++;
  return ans;
}
const possibleStringCount = solve;
class Solution { possibleStringCount(word) { return solve(word); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, possibleStringCount };
