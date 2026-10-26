'use strict';

// 1385. Find the Distance Value Between Two Arrays (Easy).
// Specification: https://leetcode.com/problems/find-the-distance-value-between-two-arrays/description/
// O(m log m + n log m) time, O(m) space; n=len(arr1), m=len(arr2); preserve inputs.
function solve(arr1, arr2, d) {
  const values = arr2.slice().sort((a, b) => a - b);
  let result = 0;
  for (const value of arr1) {
    let low = 0;
    let high = values.length;
    while (low < high) {
      const middle = low + Math.floor((high - low) / 2);
      if (values[middle] < value - d) low = middle + 1;
      else high = middle;
    }
    if (low === values.length || values[low] > value + d) result++;
  }
  return result;
}

const findTheDistanceValue = solve;
class Solution {
  findTheDistanceValue(arr1, arr2, d) { return solve(arr1, arr2, d); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findTheDistanceValue };
