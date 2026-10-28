'use strict';

// 888. Fair Candy Swap (Easy).
// Specification: https://leetcode.com/problems/fair-candy-swap/description/
function solve(aliceSizes, bobSizes) {
  const sumA = aliceSizes.reduce((s, v) => s + v, 0);
  const sumB = bobSizes.reduce((s, v) => s + v, 0);
  if ((sumA - sumB) % 2 !== 0) return [];
  const diff = (sumA - sumB) / 2;
  const bobSet = new Set(bobSizes);
  for (const a of aliceSizes) { if (bobSet.has(a - diff)) return [a, a - diff]; }
  return [];
}
const fairCandySwap = solve;
class Solution { fairCandySwap(aliceSizes, bobSizes) { return solve(aliceSizes, bobSizes); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, fairCandySwap };
