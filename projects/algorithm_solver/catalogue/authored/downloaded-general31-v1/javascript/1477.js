'use strict';

// 1477. Find Two Non-overlapping Sub-arrays Each With Target Sum (Medium).
// Specification: https://leetcode.com/problems/find-two-non-overlapping-sub-arrays-each-with-target-sum/description/
function solve(arr, target) {
  const intervals = [];
  for (let start = 0; start < arr.length; start++) {
    let total = 0;
    for (let end = start; end < arr.length; end++) {
      total += arr[end];
      if (total === target) intervals.push([start, end, end - start + 1]);
    }
  }
  let best = Infinity;
  for (let i = 0; i < intervals.length; i++) {
    for (let j = 0; j < intervals.length; j++) {
      if (intervals[i][1] < intervals[j][0] || intervals[j][1] < intervals[i][0]) {
        best = Math.min(best, intervals[i][2] + intervals[j][2]);
      }
    }
  }
  return best === Infinity ? -1 : best;
}
const minSumOfLengths = solve;
class Solution { minSumOfLengths(arr, target) { return solve(arr, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSumOfLengths };
