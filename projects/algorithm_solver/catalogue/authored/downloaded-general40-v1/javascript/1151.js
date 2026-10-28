'use strict';

// 1151. Minimum Swaps to Group All 1's Together (Medium).
// Specification: https://leetcode.com/problems/minimum-swaps-to-group-all-1s-together/description/
function solve(data) {
  const total = data.reduce((a, b) => a + b, 0);
  if (total <= 1) return 0;
  let zeros = 0;
  for (let i = 0; i < total; i++) if (data[i] === 0) zeros++;
  let best = zeros;
  for (let i = total; i < data.length; i++) {
    if (data[i] === 0) zeros++;
    if (data[i - total] === 0) zeros--;
    best = Math.min(best, zeros);
  }
  return best;
}
const minSwaps = solve;
class Solution { minSwaps(data) { return solve(data); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSwaps };
