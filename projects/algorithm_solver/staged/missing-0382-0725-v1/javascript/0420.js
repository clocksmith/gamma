'use strict';

// 420. Strong Password Checker. Allocate deletions by repeated-run lengths modulo three.

function solve(password) {
  let missing = Number(!/[a-z]/.test(password)) + Number(!/[A-Z]/.test(password)) + Number(!/[0-9]/.test(password));
  const runs = [];
  for (let i = 0; i < password.length;) {
    let j = i + 1;
    while (j < password.length && password[j] === password[i]) j += 1;
    if (j - i >= 3) runs.push(j - i);
    i = j;
  }
  if (password.length < 6) return Math.max(missing, 6 - password.length);
  let replacements = runs.reduce((sum, length) => sum + Math.floor(length / 3), 0);
  if (password.length <= 20) return Math.max(missing, replacements);
  const deletions = password.length - 20;
  let remaining = deletions;
  let use = Math.min(remaining, runs.filter(length => length % 3 === 0).length);
  replacements -= use; remaining -= use;
  use = Math.min(Math.floor(remaining / 2), runs.filter(length => length % 3 === 1).length);
  replacements -= use; remaining -= 2 * use;
  replacements -= Math.min(replacements, Math.floor(remaining / 3));
  return deletions + Math.max(missing, replacements);
}

const strongPasswordChecker = solve;
class Solution {
  strongPasswordChecker(password) { return solve(password); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, strongPasswordChecker };
