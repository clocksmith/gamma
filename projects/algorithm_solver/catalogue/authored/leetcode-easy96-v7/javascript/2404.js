'use strict';

// 2404. Most Frequent Even Element (Easy).
// Specification: https://leetcode.com/problems/most-frequent-even-element/description/
// O(n) expected time, O(n) space; break frequency ties by smaller value; preserve nums.
function solve(nums) {
  const counts = new Map();
  let best = -1;
  let largestCount = 0;
  for (const value of nums) {
    if (value % 2 !== 0) continue;
    const count = (counts.get(value) || 0) + 1;
    counts.set(value, count);
    if (count > largestCount || (count === largestCount && value < best)) {
      largestCount = count;
      best = value;
    }
  }
  return best;
}

const mostFrequentEven = solve;
class Solution {
  mostFrequentEven(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostFrequentEven };
