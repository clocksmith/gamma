'use strict';

// 826. Most Profit Assigning Work (Medium).
// Specification: https://leetcode.com/problems/most-profit-assigning-work/description/
function solve(difficulty, profit, worker) {
  const jobs = difficulty.map((d, i) => [d, profit[i]]).sort((a, b) => a[0] - b[0]);
  const sortedWorkers = worker.slice().sort((a, b) => a - b);
  let best = 0; let jobIndex = 0; let total = 0;
  for (const ability of sortedWorkers) {
    while (jobIndex < jobs.length && jobs[jobIndex][0] <= ability) { best = Math.max(best, jobs[jobIndex][1]); jobIndex++; }
    total += best;
  }
  return total;
}
const maxProfitAssignment = solve;
class Solution { maxProfitAssignment(difficulty, profit, worker) { return solve(difficulty, profit, worker); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProfitAssignment };
