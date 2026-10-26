'use strict';

// 3852. Smallest Pair With Different Frequencies (Easy).
// Specification: https://leetcode.com/problems/smallest-pair-with-different-frequencies/description/
// O(n + 100) time, O(100) space; preserve nums and return the lexicographically smallest pair.
function solve(nums) {
  const counts = new Array(101).fill(0);
  for (const value of nums) counts[value]++;
  let smallest = 1;
  while (counts[smallest] === 0) smallest++;
  for (let value = smallest + 1; value <= 100; value++) {
    if (counts[value] > 0 && counts[value] !== counts[smallest]) {
      return [smallest, value];
    }
  }
  return [-1, -1];
}

const minDistinctFreqPair = solve;
class Solution {
  minDistinctFreqPair(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDistinctFreqPair };
