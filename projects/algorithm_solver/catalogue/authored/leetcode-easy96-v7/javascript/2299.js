'use strict';

// 2299. Strong Password Checker II (Easy).
// Specification: https://leetcode.com/problems/strong-password-checker-ii/description/
// O(n) time, O(1) space; require four ASCII character categories and no equal adjacent characters.
function solve(password) {
  if (password.length < 8) return false;
  let lowercase = false;
  let uppercase = false;
  let digit = false;
  let special = false;
  const symbols = '!@#$%^&*()-+';
  for (let index = 0; index < password.length; index++) {
    const character = password[index];
    if (index > 0 && character === password[index - 1]) return false;
    if (character >= 'a' && character <= 'z') lowercase = true;
    else if (character >= 'A' && character <= 'Z') uppercase = true;
    else if (character >= '0' && character <= '9') digit = true;
    else if (symbols.includes(character)) special = true;
  }
  return lowercase && uppercase && digit && special;
}

const strongPasswordCheckerII = solve;
class Solution {
  strongPasswordCheckerII(password) { return solve(password); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, strongPasswordCheckerII };
