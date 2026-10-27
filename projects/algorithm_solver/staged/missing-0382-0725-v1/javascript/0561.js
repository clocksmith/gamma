'use strict';

// 561. Array Partition. Pair adjacent sorted values; preserve the original array.

function solve(nums) {
  const ordered = nums.slice().sort((a, b) => a - b);
  let answer = 0;
  for (let i = 0; i < ordered.length; i += 2) answer += ordered[i];
  return answer;
}

const arrayPairSum = solve;
class Solution {
  arrayPairSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, arrayPairSum };
