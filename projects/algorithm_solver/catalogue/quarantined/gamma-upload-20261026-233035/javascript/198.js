'use strict';
// 198. House Robber.
function solve(nums) {
  let previous = 0; let current = 0;
  for (const value of nums) [previous, current] = [current, Math.max(current, previous + value)];
  return current;
}
const rob = solve;
class Solution { rob(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rob };
