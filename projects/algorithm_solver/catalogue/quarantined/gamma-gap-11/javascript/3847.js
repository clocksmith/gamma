'use strict';

// 3847. Find the Score Difference in a Game.
// O(n) time and O(1) space; apply both role changes before awarding each score.
function solve(nums) {
  let active = 1;
  let answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    if (nums[index] % 2 !== 0) active = -active;
    if ((index + 1) % 6 === 0) active = -active;
    answer += active * nums[index];
  }
  return answer;
}

const scoreDifference = solve;
class Solution {
  scoreDifference(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, scoreDifference };
