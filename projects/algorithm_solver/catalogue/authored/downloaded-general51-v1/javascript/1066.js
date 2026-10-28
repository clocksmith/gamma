'use strict';

// 1066. Campus Bikes II (Medium).
// Specification: https://leetcode.com/problems/campus-bikes-ii/description/
function solve(workers, bikes) {
  const memo = new Map();
  function dp(workerIndex, usedMask) {
    if (workerIndex === workers.length) return 0;
    const key = workerIndex + ',' + usedMask;
    if (memo.has(key)) return memo.get(key);
    let best = Infinity;
    for (let b = 0; b < bikes.length; b++) {
      if ((usedMask & (1 << b)) === 0) {
        const distance = Math.abs(workers[workerIndex][0] - bikes[b][0]) + Math.abs(workers[workerIndex][1] - bikes[b][1]);
        best = Math.min(best, distance + dp(workerIndex + 1, usedMask | (1 << b)));
      }
    }
    memo.set(key, best);
    return best;
  }
  return dp(0, 0);
}
const assignBikes = solve;
class Solution { assignBikes(workers, bikes) { return solve(workers, bikes); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, assignBikes };
