'use strict';

// 1328. Break a Palindrome (Medium).
// Specification: https://leetcode.com/problems/break-a-palindrome/description/
function solve(palindrome) {
  const n = palindrome.length;
  if (n === 1) return "";
  const chars = palindrome.split("");
  let i = 0;
  while (i < Math.floor(n / 2) && chars[i] === "a") i++;
  if (i === Math.floor(n / 2)) chars[n - 1] = "b"; else chars[i] = "a";
  return chars.join("");
}
const breakPalindrome = solve;
class Solution { breakPalindrome(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, breakPalindrome };
