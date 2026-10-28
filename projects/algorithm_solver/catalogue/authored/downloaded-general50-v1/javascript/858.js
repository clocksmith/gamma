'use strict';

// 858. Mirror Reflection (Medium).
// Specification: https://leetcode.com/problems/mirror-reflection/description/
function gcd(a, b) { while (b !== 0) { const t = a % b; a = b; b = t; } return a; }
function solve(p, q) {
  const lcm = p * q / gcd(p, q);
  const m = lcm / p; const n = lcm / q;
  if (m % 2 === 1 && n % 2 === 1) return 1;
  if (m % 2 === 1 && n % 2 === 0) return 2;
  return 0;
}
const mirrorReflection = solve;
class Solution { mirrorReflection(p, q) { return solve(p, q); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, mirrorReflection };
