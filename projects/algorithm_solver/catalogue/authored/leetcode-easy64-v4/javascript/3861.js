'use strict';

// 3861. Minimum Capacity Box (Easy).
// Specification: https://leetcode.com/problems/minimum-capacity-box/description/
// O(n) time, O(1) space; preserve capacity; equal capacities retain the earliest index.
function solve(capacity, itemSize) {
  let result = -1;
  for (let index = 0; index < capacity.length; index++) {
    if (capacity[index] >= itemSize && (result === -1 || capacity[index] < capacity[result])) {
      result = index;
    }
  }
  return result;
}

const minimumIndex = solve;
class Solution {
  minimumIndex(capacity, itemSize) { return solve(capacity, itemSize); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumIndex };
