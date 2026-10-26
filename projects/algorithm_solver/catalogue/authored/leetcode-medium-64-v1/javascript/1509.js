'use strict';

// 1509. Minimum Difference Between Largest and Smallest Value in Three Moves: compare the four ways to remove three sorted extremes.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  if (nums.length <= 4) return 0;
  const ordered = [...nums].sort((left, right) => left - right);
  let answer = Infinity;
  for (let left = 0; left < 4; left += 1) {
    answer = Math.min(answer, ordered[nums.length - 4 + left] - ordered[left]);
  }
  return answer;
}

const minDifference = solve;
class Solution {
  minDifference(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDifference };
