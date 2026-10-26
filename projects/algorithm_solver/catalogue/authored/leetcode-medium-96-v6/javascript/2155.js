'use strict';

// 2155. All Divisions With the Highest Score of a Binary Array: move the division while maintaining left zeros and right ones.
// O(n) time and O(n) result space; inputs are read-only.
function solve(nums) {
  let leftZeros = 0;
  let rightOnes = 0;
  for (const value of nums) rightOnes += value;
  let best = -1;
  let result = [];
  for (let index = 0; index <= nums.length; index += 1) {
    const score = leftZeros + rightOnes;
    if (score > best) {
      best = score;
      result = [index];
    } else if (score === best) result.push(index);
    if (index < nums.length) {
      if (nums[index] === 0) leftZeros += 1;
      else rightOnes -= 1;
    }
  }
  return result;
}

const maxScoreIndices = solve;
class Solution {
  maxScoreIndices(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScoreIndices };
