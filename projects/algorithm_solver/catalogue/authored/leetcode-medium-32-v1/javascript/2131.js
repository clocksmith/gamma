'use strict';

// 2131. Longest Palindrome by Concatenating Two Letter Words: pair reversed words and reserve one symmetric center.
// O(n) expected time and O(1) auxiliary space for 26^2 possible words; inputs are read-only.
function solve(words) {
  const unmatched = new Map();
  let length = 0;
  for (const word of words) {
    const reverse = word[1] + word[0];
    const available = unmatched.get(reverse) || 0;
    if (available > 0) {
      unmatched.set(reverse, available - 1);
      length += 4;
    } else {
      unmatched.set(word, (unmatched.get(word) || 0) + 1);
    }
  }
  for (const [word, count] of unmatched) {
    if (count > 0 && word[0] === word[1]) return length + 2;
  }
  return length;
}

const longestPalindrome = solve;
class Solution {
  longestPalindrome(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestPalindrome };
