'use strict';

// 2323. Find Minimum Time to Finish All Jobs II: match sorted job sizes to sorted worker rates.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(jobs, workers) {
  const orderedJobs = [...jobs].sort((left, right) => left - right);
  const orderedWorkers = [...workers].sort((left, right) => left - right);
  let answer = 0;
  for (let index = 0; index < orderedJobs.length; index += 1) {
    const rate = orderedWorkers[index];
    answer = Math.max(answer, Math.floor((orderedJobs[index] + rate - 1) / rate));
  }
  return answer;
}

const minimumTime = solve;
class Solution {
  minimumTime(jobs, workers) { return solve(jobs, workers); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTime };
