'use strict';

// 2207. Maximize Number of Subsequences in a String: count existing pairs then choose the better endpoint insertion.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(text, pattern) {
  let firstCount = 0;
  let secondCount = 0;
  let answer = 0;
  for (const character of text) {
    // This ordering also handles a pattern with two identical characters.
    if (character === pattern[1]) {
      answer += firstCount;
      secondCount += 1;
    }
    if (character === pattern[0]) firstCount += 1;
  }
  return answer + Math.max(firstCount, secondCount);
}

const maximumSubsequenceCount = solve;
class Solution {
  maximumSubsequenceCount(text, pattern) { return solve(text, pattern); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSubsequenceCount };
