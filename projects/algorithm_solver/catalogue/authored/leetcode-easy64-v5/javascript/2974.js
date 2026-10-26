'use strict';

// 2974. Minimum Number Game (Easy).
// Specification: https://leetcode.com/problems/minimum-number-game/description/
// O(n log n) time, O(n) space; sort a copy and swap adjacent pairs.
function solve(nums) {
  const result = nums.slice().sort((left, right) => left - right);
  for (let index = 0; index < result.length; index += 2) {
    const smaller = result[index];
    result[index] = result[index + 1];
    result[index + 1] = smaller;
  }
  return result;
}

const numberGame = solve;
class Solution {
  numberGame(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberGame };
