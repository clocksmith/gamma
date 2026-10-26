'use strict';

// 2244. Minimum Rounds to Complete All Tasks: group each frequency into triples with pairs for the remainder.
// O(n) expected time and O(u) auxiliary space for u distinct difficulties; inputs are read-only.
function solve(tasks) {
  const counts = new Map();
  for (const task of tasks) counts.set(task, (counts.get(task) || 0) + 1);
  let answer = 0;
  for (const count of counts.values()) {
    if (count === 1) return -1;
    answer += Math.floor((count + 2) / 3);
  }
  return answer;
}

const minimumRounds = solve;
class Solution {
  minimumRounds(tasks) { return solve(tasks); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumRounds };
