'use strict';

// 1371. Find the Longest Substring Containing Vowels in Even Counts: match the earliest occurrence of each vowel-parity mask.
// O(n) time and O(1) auxiliary space for 32 masks; inputs are read-only.
function solve(s) {
  const bits = { a: 1, e: 2, i: 4, o: 8, u: 16 };
  const first = new Array(32).fill(-2);
  first[0] = -1;
  let mask = 0;
  let answer = 0;
  for (let index = 0; index < s.length; index += 1) {
    mask ^= bits[s[index]] || 0;
    if (first[mask] === -2) first[mask] = index;
    else answer = Math.max(answer, index - first[mask]);
  }
  return answer;
}

const findTheLongestSubstring = solve;
class Solution {
  findTheLongestSubstring(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findTheLongestSubstring };
