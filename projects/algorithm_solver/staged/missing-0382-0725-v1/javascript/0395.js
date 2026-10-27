'use strict';

// 395. Longest Substring with At Least K Repeating Characters. Enumerate the number of distinct lowercase letters; O(26*n) time.

function solve(s, k) {
  let answer = 0;
  for (let wanted = 1; wanted <= new Set(s).size; wanted += 1) {
    const counts = Array(26).fill(0);
    let left = 0, distinct = 0, sufficient = 0;
    for (let right = 0; right < s.length; right += 1) {
      let index = s.charCodeAt(right) - 97;
      if (counts[index] === 0) distinct += 1;
      counts[index] += 1;
      if (counts[index] === k) sufficient += 1;
      while (distinct > wanted) {
        index = s.charCodeAt(left) - 97;
        if (counts[index] === k) sufficient -= 1;
        counts[index] -= 1;
        if (counts[index] === 0) distinct -= 1;
        left += 1;
      }
      if (distinct === sufficient) answer = Math.max(answer, right - left + 1);
    }
  }
  return answer;
}

const longestSubstring = solve;
class Solution {
  longestSubstring(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubstring };
