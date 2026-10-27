'use strict';

// 414. Third Maximum Number. Keep only the three largest distinct values.

function solve(nums) {
  const top = [];
  for (const value of nums) {
    if (!top.includes(value)) {
      top.push(value); top.sort((a, b) => b - a);
      if (top.length > 3) top.pop();
    }
  }
  return top.length === 3 ? top[2] : top[0];
}

const thirdMax = solve;
class Solution {
  thirdMax(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, thirdMax };
