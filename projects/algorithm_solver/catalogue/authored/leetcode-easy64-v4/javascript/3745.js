'use strict';

// 3745. Maximize Expression of Three Elements (Easy).
// Specification: https://leetcode.com/problems/maximize-expression-of-three-elements/description/
// O(n) time, O(1) space; track two maximum occurrences and one minimum; preserve nums.
function solve(nums) {
  let largest = -Infinity;
  let secondLargest = -Infinity;
  let smallest = Infinity;
  for (const value of nums) {
    smallest = Math.min(smallest, value);
    if (value >= largest) {
      secondLargest = largest;
      largest = value;
    } else if (value > secondLargest) {
      secondLargest = value;
    }
  }
  return largest + secondLargest - smallest;
}

const maximizeExpressionOfThree = solve;
class Solution {
  maximizeExpressionOfThree(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximizeExpressionOfThree };
