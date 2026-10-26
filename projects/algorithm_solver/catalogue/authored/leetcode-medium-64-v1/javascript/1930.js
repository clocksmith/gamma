'use strict';

// 1930. Unique Length-3 Palindromic Subsequences: count distinct middle letters between each outer letter first and last occurrence.
// O(26 * n) time and O(1) auxiliary space for lowercase English letters; inputs are read-only.
function solve(s) {
  const first = new Array(26).fill(-1);
  const last = new Array(26).fill(-1);
  for (let index = 0; index < s.length; index += 1) {
    const letter = s.charCodeAt(index) - 97;
    if (first[letter] === -1) first[letter] = index;
    last[letter] = index;
  }
  let answer = 0;
  for (let letter = 0; letter < 26; letter += 1) {
    if (last[letter] - first[letter] < 2) continue;
    let middleMask = 0;
    for (let index = first[letter] + 1; index < last[letter]; index += 1) {
      middleMask |= 1 << (s.charCodeAt(index) - 97);
    }
    while (middleMask) {
      answer += 1;
      middleMask &= middleMask - 1;
    }
  }
  return answer;
}

const countPalindromicSubsequence = solve;
class Solution {
  countPalindromicSubsequence(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPalindromicSubsequence };
