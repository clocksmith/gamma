'use strict';

// 486. Predict the Winner. Interval minimax expressed as the current player's score advantage.

function solve(nums) {
  const dp = nums.slice();
  for (let left = nums.length - 2; left >= 0; left -= 1) {
    for (let right = left + 1; right < nums.length; right += 1) {
      dp[right] = Math.max(nums[left] - dp[right], nums[right] - dp[right - 1]);
    }
  }
  return nums.length === 0 || dp[dp.length - 1] >= 0;
}

const predictTheWinner = solve;
class Solution {
  predictTheWinner(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, predictTheWinner };
