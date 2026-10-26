'use strict';

// 3640. Trionic Array II.
// Track nonempty increasing, decreasing-after-increasing, and final increasing phases; O(n) time and O(1) space. Each phase requires an edge. Inputs are preserved.

function solve(nums) {
  let increasing = -Infinity, decreasing = -Infinity, final = -Infinity, answer = -Infinity;
  for (let index = 1; index < nums.length; index += 1) {
    const previous = nums[index - 1], value = nums[index];
    if (value > previous) {
      const nextIncreasing = Math.max(previous + value, increasing + value), nextFinal = Math.max(decreasing, final) + value;
      increasing = nextIncreasing; decreasing = -Infinity; final = nextFinal;
    } else if (value < previous) {
      decreasing = Math.max(increasing, decreasing) + value;
      increasing = -Infinity; final = -Infinity;
    } else {
      increasing = -Infinity; decreasing = -Infinity; final = -Infinity;
    }
    answer = Math.max(answer, final);
  }
  return answer;
}

const maxSumTrionic = solve;
class Solution {
  maxSumTrionic(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSumTrionic };
