'use strict';

// 2951. Find the Peaks (Easy).
// Specification: https://leetcode.com/problems/find-the-peaks/description/
// O(n) time, O(n) result space; return ascending indices and preserve mountain.
function solve(mountain) {
  const peaks = [];
  for (let index = 1; index + 1 < mountain.length; index++) {
    if (mountain[index] > mountain[index - 1] && mountain[index] > mountain[index + 1]) {
      peaks.push(index);
    }
  }
  return peaks;
}

const findPeaks = solve;
class Solution {
  findPeaks(mountain) { return solve(mountain); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findPeaks };
