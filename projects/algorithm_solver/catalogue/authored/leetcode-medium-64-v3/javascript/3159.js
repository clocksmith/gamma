'use strict';

// 3159. Find Occurrences of an Element in an Array: index matching positions once and answer one-based occurrence queries.
// O(n + q) time and O(n + q) space including output; inputs are read-only.
function solve(nums, queries, x) {
  const positions = [];
  for (let index = 0; index < nums.length; index += 1) {
    if (nums[index] === x) positions.push(index);
  }
  return queries.map(query => query <= positions.length ? positions[query - 1] : -1);
}

const occurrencesOfElement = solve;
class Solution {
  occurrencesOfElement(nums, queries, x) { return solve(nums, queries, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, occurrencesOfElement };
