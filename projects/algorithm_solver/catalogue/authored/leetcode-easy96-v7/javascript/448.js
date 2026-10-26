'use strict';

// 448. Find All Numbers Disappeared in an Array (Easy).
// Specification: https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array/description/
// O(n) time and space; preserve nums and return missing values in ascending order.
function solve(nums) {
  const present = new Array(nums.length + 1).fill(false);
  for (const value of nums) present[value] = true;
  const result = [];
  for (let value = 1; value <= nums.length; value++) {
    if (!present[value]) result.push(value);
  }
  return result;
}

const findDisappearedNumbers = solve;
class Solution {
  findDisappearedNumbers(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDisappearedNumbers };
