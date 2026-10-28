'use strict';

// 831. Masking Personal Information (Medium).
// Specification: https://leetcode.com/problems/masking-personal-information/description/
function solve(s) {
  if (s.includes('@')) {
    const lower = s.toLowerCase();
    const at = lower.indexOf('@');
    return lower[0] + '*****' + lower[at - 1] + lower.slice(at);
  }
  const digits = s.replace(/\D/g, '');
  const local = digits.slice(-10);
  const country = digits.slice(0, -10);
  if (country === '') return '***-***-' + local.slice(-4);
  return '+' + '*'.repeat(country.length) + '-***-***-' + local.slice(-4);
}
const maskPII = solve;
class Solution { maskPII(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maskPII };
