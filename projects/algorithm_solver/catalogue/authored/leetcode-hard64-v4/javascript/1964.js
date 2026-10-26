'use strict';

// 1964. Find the Longest Valid Obstacle Course at Each Position. Upper-bound patience sorting for nondecreasing subsequences; O(n log n) time and O(n) space. Inputs are preserved.

function solve(obstacles) {
  const tails = [];
  const answer = [];
  for (const height of obstacles) {
    let left = 0;
    let right = tails.length;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (tails[middle] <= height) left = middle + 1;
      else right = middle;
    }
    answer.push(left + 1);
    tails[left] = height;
  }
  return answer;
}

const longestObstacleCourseAtEachPosition = solve;
class Solution {
  longestObstacleCourseAtEachPosition(obstacles) { return solve(obstacles); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestObstacleCourseAtEachPosition };
