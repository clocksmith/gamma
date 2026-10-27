'use strict';

// 4056. Number of Intersecting Interval Pairs I.
// Specification: https://leetcode.com/problems/number-of-intersecting-interval-pairs-i/description/
// O(n^2) time and O(1) auxiliary space; closed endpoints count as intersection. Inputs are preserved.
function solve(intervals) {
  let answer = 0;
  for (let first = 0; first < intervals.length; first++) {
    for (let second = first + 1; second < intervals.length; second++) {
      if (Math.max(intervals[first][0], intervals[second][0]) <= Math.min(intervals[first][1], intervals[second][1])) answer++;
    }
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
