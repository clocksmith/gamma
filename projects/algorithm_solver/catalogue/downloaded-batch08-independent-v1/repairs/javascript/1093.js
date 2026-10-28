'use strict';

// 1093. Statistics from a Large Sample (Medium).
// Specification: https://leetcode.com/problems/statistics-from-a-large-sample/description/
function solve(count) {
  let total = 0; let totalSum = 0; let minimum = -1; let maximum = -1; let mode = -1; let modeCount = -1;
  for (let i = 0; i < count.length; i++) {
    if (count[i] > 0) {
      if (minimum === -1) minimum = i;
      maximum = i;
      if (count[i] > modeCount) { modeCount = count[i]; mode = i; }
    }
    total += count[i]; totalSum += count[i] * i;
  }
  const mean = totalSum / total;
  let median = 0;
  let cumulative = 0;
  const firstMiddle = Math.floor((total + 1) / 2);
  const secondMiddle = Math.floor(total / 2) + 1;
  let firstValue = -1; let secondValue = -1;
  for (let i = 0; i < count.length; i++) {
    cumulative += count[i];
    if (firstValue === -1 && cumulative >= firstMiddle) firstValue = i;
    if (secondValue === -1 && cumulative >= secondMiddle) secondValue = i;
  }
  median = (firstValue + secondValue) / 2;
  return [minimum, maximum, mean, median, mode];
}
const sampleStats = solve;
class Solution { sampleStats(count) { return solve(count); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, sampleStats };
