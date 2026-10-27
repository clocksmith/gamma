'use strict';

// 487. Max Consecutive Ones II.

function solve(nums) {
  let left = 0, zeros = 0, answer = 0;
  for (let right = 0; right < nums.length; right += 1) {
    if (nums[right] === 0) zeros += 1;
    while (zeros > 1) { if (nums[left++] === 0) zeros -= 1; }
    answer = Math.max(answer, right - left + 1);
  }
  return answer;
}

const findMaxConsecutiveOnes = solve;
class Solution {
  findMaxConsecutiveOnes(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaxConsecutiveOnes };
