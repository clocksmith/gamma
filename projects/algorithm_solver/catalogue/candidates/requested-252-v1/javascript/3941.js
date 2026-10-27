/**
 * 3941. Password Strength
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/password-strength/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3941.Password%20Strength/README_EN.md
 * Complexity: O(n) time, O(1) bounded alphabet space.
 * Allowed alphabet: ASCII letters/digits and !@#$. A toy problem score, not a security-strength assessment.
 */

function solve(password) {
  let answer = 0;
  for (const character of new Set(password)) {
    if (character >= 'a' && character <= 'z') answer += 1;
    else if (character >= 'A' && character <= 'Z') answer += 2;
    else if (character >= '0' && character <= '9') answer += 3;
    else answer += 5;
  }
  return answer;
}

function passwordStrength(password) {
  return solve(password);
}

class Solution {
  passwordStrength(password) {
    return solve(password);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, passwordStrength, Solution };
}
