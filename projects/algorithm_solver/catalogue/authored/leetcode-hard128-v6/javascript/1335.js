'use strict';

// 1335. Minimum Difficulty of a Job Schedule.
// Partition-prefix dynamic programming; O(d*n^2) time and O(n) space. Inputs are preserved.

function solve(jobDifficulty, d) {
  const n = jobDifficulty.length;
  if (n < d) return -1;
  let costs = Array(n + 1).fill(Infinity);
  costs[0] = 0;
  for (let day = 1; day <= d; day += 1) {
    const following = Array(n + 1).fill(Infinity);
    for (let end = day; end <= n; end += 1) {
      let hardest = 0;
      for (let start = end - 1; start >= day - 1; start -= 1) {
        hardest = Math.max(hardest, jobDifficulty[start]);
        following[end] = Math.min(following[end], costs[start] + hardest);
      }
    }
    costs = following;
  }
  return costs[n];
}

const minDifficulty = solve;
class Solution {
  minDifficulty(jobDifficulty, d) { return solve(jobDifficulty, d); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDifficulty };
