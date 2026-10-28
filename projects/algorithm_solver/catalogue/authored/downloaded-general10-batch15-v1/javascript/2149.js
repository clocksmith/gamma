'use strict';

// 2149. Rearrange Array Elements by Sign (Medium).
// Specification: https://leetcode.com/problems/rearrange-array-elements-by-sign/description/
function solve(nums) {
  const positives = nums.filter((x) => x > 0);
  const negatives = nums.filter((x) => x < 0);
  const result = [];
  for (let i = 0; i < positives.length; i++) {
    result.push(positives[i]);
    if (i < negatives.length) result.push(negatives[i]);
  }
  return result.concat(negatives.slice(positives.length));
}
const rearrangeArray = solve;
class Solution { rearrangeArray(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rearrangeArray };
