'use strict';
// 229. Majority Element II.
function solve(nums) {
  let first = null; let second = null; let firstCount = 0; let secondCount = 0;
  for (const value of nums) {
    if (value === first) firstCount += 1;
    else if (value === second) secondCount += 1;
    else if (firstCount === 0) { first = value; firstCount = 1; }
    else if (secondCount === 0) { second = value; secondCount = 1; }
    else { firstCount -= 1; secondCount -= 1; }
  }
  return [first, second].filter((value, index, values) => value !== null && values.indexOf(value) === index
    && nums.reduce((count, item) => count + (item === value ? 1 : 0), 0) > Math.floor(nums.length / 3));
}
const majorityElement = solve;
class Solution { majorityElement(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, majorityElement };
