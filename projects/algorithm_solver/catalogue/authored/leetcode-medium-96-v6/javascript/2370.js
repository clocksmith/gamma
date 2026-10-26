'use strict';

// 2370. Longest Ideal Subsequence: retain the longest subsequence ending in each alphabet letter.
// O(n * min(26, 2k + 1)) time and O(26) auxiliary space; inputs are read-only.
function solve(s, k) {
  const best = new Int32Array(26);
  for (const character of s) {
    const letter = character.charCodeAt(0) - 97;
    let length = 0;
    for (let previous = Math.max(0, letter - k); previous <= Math.min(25, letter + k); previous += 1) {
      length = Math.max(length, best[previous]);
    }
    best[letter] = length + 1;
  }
  let answer = 0;
  for (const length of best) answer = Math.max(answer, length);
  return answer;
}

const longestIdealString = solve;
class Solution {
  longestIdealString(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestIdealString };
