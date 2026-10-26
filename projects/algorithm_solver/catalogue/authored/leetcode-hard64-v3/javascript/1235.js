'use strict';

// 1235. Maximum Profit in Job Scheduling: weighted interval scheduling; O(n log n) time and O(n) space. Inputs are preserved.

function solve(startTime, endTime, profit) {
  const jobs = startTime.map((start, index) => [start, endTime[index], profit[index]]);
  jobs.sort((a, b) => a[0] - b[0]);
  const best = Array(jobs.length + 1).fill(0);
  for (let index = jobs.length - 1; index >= 0; index -= 1) {
    const [, end, value] = jobs[index];
    let left = index + 1;
    let right = jobs.length;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (jobs[middle][0] < end) left = middle + 1;
      else right = middle;
    }
    best[index] = Math.max(best[index + 1], value + best[left]);
  }
  return best[0];
}

const jobScheduling = solve;
class Solution {
  jobScheduling(startTime, endTime, profit) { return solve(startTime, endTime, profit); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, jobScheduling };
