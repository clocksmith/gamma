'use strict';

// 970. Powerful Integers (Medium).
// Specification: https://leetcode.com/problems/powerful-integers/description/
function solve(x, y, bound) {
  const result = new Set();
  const xPowers = []; let value = 1;
  while (value <= bound) { xPowers.push(value); if (x === 1) break; value *= x; }
  const yPowers = []; value = 1;
  while (value <= bound) { yPowers.push(value); if (y === 1) break; value *= y; }
  for (const a of xPowers) { for (const b of yPowers) { if (a + b <= bound) result.add(a + b); } }
  return [...result].sort((a, b) => a - b);
}
const powerfulIntegers = solve;
class Solution { powerfulIntegers(x, y, bound) { return solve(x, y, bound); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, powerfulIntegers };
