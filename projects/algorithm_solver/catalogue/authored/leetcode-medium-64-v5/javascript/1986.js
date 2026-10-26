'use strict';

// 1986. Minimum Number of Work Sessions to Finish the Tasks: minimize the session count and then the current load for every task subset.
// O(n * 2^n) time and O(2^n) auxiliary space; inputs are read-only.
function solve(tasks, sessionTime) {
  const count = tasks.length;
  const size = 1 << count;
  const sessions = new Int32Array(size).fill(count + 1);
  const used = new Int32Array(size).fill(sessionTime);
  sessions[0] = 1;
  used[0] = 0;
  for (let mask = 0; mask < size; mask += 1) {
    for (let index = 0; index < count; index += 1) {
      const bit = 1 << index;
      if (mask & bit) continue;
      let nextSessions = sessions[mask];
      let nextUsed = used[mask] + tasks[index];
      if (nextUsed > sessionTime) {
        nextSessions += 1;
        nextUsed = tasks[index];
      }
      const next = mask | bit;
      if (nextSessions < sessions[next] || (nextSessions === sessions[next] && nextUsed < used[next])) {
        sessions[next] = nextSessions;
        used[next] = nextUsed;
      }
    }
  }
  return sessions[size - 1];
}

const minSessions = solve;
class Solution {
  minSessions(tasks, sessionTime) { return solve(tasks, sessionTime); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSessions };
