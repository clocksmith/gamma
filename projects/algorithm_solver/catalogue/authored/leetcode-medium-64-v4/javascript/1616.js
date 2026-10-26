'use strict';

// 1616. Split Two Strings to Make Palindrome: match cross-string ends then test either remaining middle.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(a, b) {
  function palindrome(text, left, right) {
    while (left < right) {
      if (text[left] !== text[right]) return false;
      left += 1;
      right -= 1;
    }
    return true;
  }
  function compatible(first, second) {
    let left = 0;
    let right = first.length - 1;
    while (left < right && first[left] === second[right]) {
      left += 1;
      right -= 1;
    }
    return palindrome(first, left, right) || palindrome(second, left, right);
  }
  return compatible(a, b) || compatible(b, a);
}

const checkPalindromeFormation = solve;
class Solution {
  checkPalindromeFormation(a, b) { return solve(a, b); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkPalindromeFormation };
