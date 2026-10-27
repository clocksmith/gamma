'use strict';
// 125. Valid Palindrome.
function solve(s) {
  let left = 0;
  let right = s.length - 1;
  const alphaNumeric = character => /[0-9A-Za-z]/.test(character);
  while (left < right) {
    while (left < right && !alphaNumeric(s[left])) left += 1;
    while (left < right && !alphaNumeric(s[right])) right -= 1;
    if (s[left].toLowerCase() !== s[right].toLowerCase()) return false;
    left += 1; right -= 1;
  }
  return true;
}
const isPalindrome = solve;
class Solution { isPalindrome(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPalindrome };
