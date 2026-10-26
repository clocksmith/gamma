'use strict';

// 3727. Maximum Alternating Sum of Squares.
// O(n log n) time and O(n) auxiliary space; inputs are preserved and totals fit safe integers.
function solve(nums) {
  const squares = nums.map(value => value * value).sort((left, right) => left - right);
  const negative = Math.floor(nums.length / 2);
  let answer = 0;
  for (let index = 0; index < squares.length; index += 1) answer += index < negative ? -squares[index] : squares[index];
  return answer;
}

const maxAlternatingSum = solve;
class Solution {
  maxAlternatingSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxAlternatingSum };
