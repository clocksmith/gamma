'use strict';

// 1422. Maximum Score After Splitting a String (Easy).
// Specification: https://leetcode.com/problems/maximum-score-after-splitting-a-string/description/
// O(n) time, O(1) auxiliary space; both split parts remain nonempty.
function solve(s) {
  let rightOnes = 0;
  for (const character of s) {
    if (character === '1') rightOnes++;
  }
  let leftZeros = 0;
  let result = 0;
  for (let index = 0; index < s.length - 1; index++) {
    if (s[index] === '0') leftZeros++;
    else rightOnes--;
    result = Math.max(result, leftZeros + rightOnes);
  }
  return result;
}

const maxScore = solve;
class Solution {
  maxScore(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
