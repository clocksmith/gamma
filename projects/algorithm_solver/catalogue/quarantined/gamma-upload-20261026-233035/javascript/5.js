'use strict';
// 5. Longest Palindromic Substring.
function solve(s) {
  let start = 0;
  let end = 0;
  for (let center = 0; center < s.length; center += 1) {
    for (const offset of [0, 1]) {
      let left = center;
      let right = center + offset;
      while (left >= 0 && right < s.length && s[left] === s[right]) { left -= 1; right += 1; }
      if (right - left - 1 > end - start + 1) { start = left + 1; end = right - 1; }
    }
  }
  return s.slice(start, end + 1);
}
const longestPalindrome = solve;
class Solution { longestPalindrome(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestPalindrome };
