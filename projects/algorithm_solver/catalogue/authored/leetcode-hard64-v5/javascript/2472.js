'use strict';

// 2472. Maximum Number of Non-overlapping Palindrome Substrings. Earliest-finish greedy over palindromes of length k or k+1; O(n*k) time and O(1) space. Inputs are preserved.

function solve(s, k) {
  function palindrome(left, right) {
    while (left < right) {
      if (s[left] !== s[right]) return false;
      left += 1;
      right -= 1;
    }
    return true;
  }
  let answer = 0;
  let available = 0;
  for (let right = k - 1; right < s.length; right += 1) {
    // Every longer palindrome contains an inner palindrome of length k or k+1.
    for (const length of [k, k + 1]) {
      const left = right - length + 1;
      if (left >= available && palindrome(left, right)) {
        answer += 1;
        available = right + 1;
        break;
      }
    }
  }
  return answer;
}

const maxPalindromes = solve;
class Solution {
  maxPalindromes(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPalindromes };
