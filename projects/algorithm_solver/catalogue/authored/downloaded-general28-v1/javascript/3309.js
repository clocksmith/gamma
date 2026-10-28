'use strict';

// 3309. Maximum Possible Number by Binary Concatenation (Medium).
// Specification: https://leetcode.com/problems/maximum-possible-number-by-binary-concatenation/description/
function solve(nums) {
  const bins = nums.map((x) => x.toString(2));
  let best = 0;
  const perm = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]];
  for (const p of perm) {
    const val = parseInt(p.map((i) => bins[i]).join(''), 2);
    if (val > best) best = val;
  }
  return best;
}
const maxGoodNumber = solve;
class Solution { maxGoodNumber(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxGoodNumber };
