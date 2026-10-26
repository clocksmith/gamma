'use strict';

// 1365. How Many Numbers Are Smaller Than the Current Number (Easy).
// Specification: https://leetcode.com/problems/how-many-numbers-are-smaller-than-the-current-number/description/
// O(n + 101) time, O(n + 101) space; preserve nums in the domain 0..100.
function solve(nums) {
  const counts = new Array(101).fill(0);
  for (const value of nums) counts[value]++;
  let smaller = 0;
  for (let value = 0; value < counts.length; value++) {
    const frequency = counts[value];
    counts[value] = smaller;
    smaller += frequency;
  }
  return nums.map(value => counts[value]);
}

const smallerNumbersThanCurrent = solve;
class Solution {
  smallerNumbersThanCurrent(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallerNumbersThanCurrent };
