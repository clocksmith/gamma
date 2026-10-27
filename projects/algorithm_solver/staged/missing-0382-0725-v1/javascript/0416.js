'use strict';

// 416. Partition Equal Subset Sum. Descending 0/1 subset-sum dynamic programming.

function solve(nums) {
  const total = nums.reduce((sum, value) => sum + value, 0);
  if (total % 2 !== 0) return false;
  const target = total / 2;
  const possible = new Uint8Array(target + 1);
  possible[0] = 1;
  for (const value of nums) {
    for (let sum = target; sum >= value; sum -= 1) {
      if (possible[sum - value]) possible[sum] = 1;
    }
  }
  return possible[target] === 1;
}

const canPartition = solve;
class Solution {
  canPartition(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canPartition };
