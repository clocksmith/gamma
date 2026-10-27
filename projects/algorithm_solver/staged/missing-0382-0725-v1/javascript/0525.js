'use strict';

// 525. Contiguous Array.

function solve(nums) {
  const first = new Map([[0, -1]]);
  let balance = 0, answer = 0;
  for (let i = 0; i < nums.length; i += 1) {
    balance += nums[i] ? 1 : -1;
    if (first.has(balance)) answer = Math.max(answer, i - first.get(balance));
    else first.set(balance, i);
  }
  return answer;
}

const findMaxLength = solve;
class Solution {
  findMaxLength(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaxLength };
