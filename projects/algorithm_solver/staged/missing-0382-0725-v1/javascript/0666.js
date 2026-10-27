'use strict';

// 666. Path Sum IV.

function solve(nums) {
  const values = new Map(nums.map(number => [Math.floor(number / 10), number % 10])), stack = [[11, 0]];
  let answer = 0;
  while (stack.length > 0) {
    let [key, total] = stack.pop();
    total += values.get(key);
    const depth = Math.floor(key / 10), position = key % 10;
    const left = (depth + 1) * 10 + 2 * position - 1, right = left + 1;
    if (!values.has(left) && !values.has(right)) answer += total;
    if (values.has(left)) stack.push([left, total]); if (values.has(right)) stack.push([right, total]);
  }
  return answer;
}

const pathSum = solve;
class Solution {
  pathSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, pathSum };
