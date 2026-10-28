'use strict';

// 167. Two Sum II - Input Array Is Sorted (Medium).
// Specification: https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/description/
function solve(numbers, target) {
  let left = 0; let right = numbers.length - 1;
  while (left < right) {
    const total = numbers[left] + numbers[right];
    if (total === target) return [left + 1, right + 1];
    if (total < target) left++;
    else right--;
  }
  return [];
}
const twoSum = solve;
class Solution { twoSum(numbers, target) { return solve(numbers, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, twoSum };
