'use strict';

// 1090. Largest Values From Labels (Medium).
// Specification: https://leetcode.com/problems/largest-values-from-labels/description/
function solve(values, labels, numWanted, useLimit) {
  const items = values.map((value, i) => [value, labels[i]]).sort((a, b) => b[0] - a[0]);
  const counts = new Map();
  let total = 0; let taken = 0;
  for (const [value, label] of items) {
    if (taken >= numWanted) break;
    const used = counts.get(label) || 0;
    if (used < useLimit) { total += value; counts.set(label, used + 1); taken++; }
  }
  return total;
}
const largestValsFromLabels = solve;
class Solution { largestValsFromLabels(values, labels, numWanted, useLimit) { return solve(values, labels, numWanted, useLimit); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestValsFromLabels };
