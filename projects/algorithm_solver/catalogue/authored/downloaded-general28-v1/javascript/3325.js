'use strict';

// 3325. Count Substrings With K-Frequency Characters I (Medium).
// Specification: https://leetcode.com/problems/count-substrings-with-k-frequency-characters-i/description/
function solve(s, k) {
  const count = new Map();
  let left = 0; let ans = 0;
  for (let right = 0; right < s.length; right++) {
    const ch = s[right];
    count.set(ch, (count.get(ch) || 0) + 1);
    while ((count.get(ch) || 0) >= k) {
      const lc = s[left];
      count.set(lc, count.get(lc) - 1);
      left++;
    }
    ans += left;
  }
  return ans;
}
const numberOfSubstrings = solve;
class Solution { numberOfSubstrings(s, k) { return solve(s, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfSubstrings };
