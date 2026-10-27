'use strict';

// 517. Super Washing Machines.

function solve(machines) {
  const total = machines.reduce((sum, value) => sum + value, 0);
  if (total % machines.length !== 0) return -1;
  const average = total / machines.length;
  let balance = 0, answer = 0;
  for (const value of machines) {
    const surplus = value - average;
    balance += surplus;
    answer = Math.max(answer, Math.abs(balance), surplus);
  }
  return answer;
}

const findMinMoves = solve;
class Solution {
  findMinMoves(machines) { return solve(machines); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMinMoves };
