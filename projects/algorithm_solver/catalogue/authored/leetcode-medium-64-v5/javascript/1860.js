'use strict';

// 1860. Incremental Memory Leak: consume each successive allocation from the larger remaining stick with first-stick ties.
// O(sqrt(memory1 + memory2 + 1)) time and O(1) auxiliary space; inputs are read-only.
function solve(memory1, memory2) {
  let first = memory1;
  let second = memory2;
  let time = 1;
  while (Math.max(first, second) >= time) {
    if (first >= second) first -= time;
    else second -= time;
    time += 1;
  }
  return [time, first, second];
}

const memLeak = solve;
class Solution {
  memLeak(memory1, memory2) { return solve(memory1, memory2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, memLeak };
