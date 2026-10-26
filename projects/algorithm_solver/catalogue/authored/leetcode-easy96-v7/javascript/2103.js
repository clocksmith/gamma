'use strict';

// 2103. Rings and Rods (Easy).
// Specification: https://leetcode.com/problems/rings-and-rods/description/
// O(n) time, O(1) space; use a three-bit color mask for each of ten rods.
function solve(rings) {
  const rods = new Array(10).fill(0);
  const colors = { R: 1, G: 2, B: 4 };
  for (let index = 0; index < rings.length; index += 2) {
    const rod = rings.charCodeAt(index + 1) - 48;
    rods[rod] |= colors[rings[index]];
  }
  let total = 0;
  for (const mask of rods) {
    if (mask === 7) total++;
  }
  return total;
}

const countPoints = solve;
class Solution {
  countPoints(rings) { return solve(rings); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPoints };
