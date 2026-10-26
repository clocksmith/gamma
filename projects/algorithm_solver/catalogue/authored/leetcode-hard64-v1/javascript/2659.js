'use strict';

// 2659. Make Array Empty: sorted removal order and remaining-length charges at wraps.
// O(n log n) time and O(n) auxiliary space; the problem requires distinct values. Inputs are preserved.
function solve(nums) {
  const length = nums.length;
  const order = Array.from({ length }, (_, index) => index).sort((a, b) => nums[a] - nums[b]);
  let answer = length;
  for (let position = 1; position < length; position += 1) {
    if (order[position] < order[position - 1]) answer += length - position;
  }
  return answer;
}

const countOperationsToEmptyArray = solve;
class Solution {
  countOperationsToEmptyArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countOperationsToEmptyArray };
