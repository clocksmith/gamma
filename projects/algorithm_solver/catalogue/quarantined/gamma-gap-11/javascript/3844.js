'use strict';

// 3844. Longest Almost-Palindromic Substring.
// O(n^2) time and O(n) space; rolling palindrome and exactly-one-deletion interval states.
function solve(s) {
  const n = s.length;
  let previousPalindrome = new Uint8Array(n);
  let previousAlmost = new Uint8Array(n);
  let answer = 1;
  for (let left = n - 1; left >= 0; left -= 1) {
    const palindrome = new Uint8Array(n);
    const almost = new Uint8Array(n);
    palindrome[left] = 1;
    almost[left] = 1;
    for (let right = left + 1; right < n; right += 1) {
      const match = s[left] === s[right];
      palindrome[right] = Number(match && (right === left + 1 || previousPalindrome[right - 1] !== 0));
      almost[right] = Number(previousPalindrome[right] !== 0 || palindrome[right - 1] !== 0 || (match && (right === left + 1 || previousAlmost[right - 1] !== 0)));
      if (almost[right] !== 0) answer = Math.max(answer, right - left + 1);
    }
    previousPalindrome = palindrome;
    previousAlmost = almost;
  }
  return answer;
}

const almostPalindromic = solve;
class Solution {
  almostPalindromic(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, almostPalindromic };
