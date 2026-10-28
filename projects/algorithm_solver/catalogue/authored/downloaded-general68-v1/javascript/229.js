'use strict';

// 229. Majority Element II (Medium).
// Specification: https://leetcode.com/problems/majority-element-ii/description/
function solve(nums) {
  let count1 = 0; let count2 = 0; let candidate1 = null; let candidate2 = null;
  for (const value of nums) {
    if (candidate1 === value) count1++;
    else if (candidate2 === value) count2++;
    else if (count1 === 0) { candidate1 = value; count1 = 1; }
    else if (count2 === 0) { candidate2 = value; count2 = 1; }
    else { count1--; count2--; }
  }
  const result = [];
  for (const candidate of [candidate1, candidate2]) {
    if (candidate !== null && nums.filter((v) => v === candidate).length > Math.floor(nums.length / 3)) result.push(candidate);
  }
  return result.sort((a, b) => a - b);
}
const majorityElement = solve;
class Solution { majorityElement(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, majorityElement };
