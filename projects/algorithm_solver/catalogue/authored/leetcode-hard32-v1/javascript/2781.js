'use strict';

// 2781. Length of the Longest Valid Substring.
// O(n*L^2 + F) expected time including slicing/hashing; L<=10, O(F+L) auxiliary space.
function solve(word, forbidden) {
  const blocked = new Set(forbidden);
  let longest = 0;
  for (const value of forbidden) longest = Math.max(longest, value.length);
  let left = 0;
  let answer = 0;
  for (let right = 0; right < word.length; right += 1) {
    const first = Math.max(left, right - longest + 1);
    for (let start = right; start >= first; start -= 1) {
      if (blocked.has(word.slice(start, right + 1))) {
        left = start + 1;
        break;
      }
    }
    answer = Math.max(answer, right - left + 1);
  }
  return answer;
}

const longestValidSubstring = solve;
class Solution {
  longestValidSubstring(word, forbidden) { return solve(word, forbidden); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestValidSubstring };
