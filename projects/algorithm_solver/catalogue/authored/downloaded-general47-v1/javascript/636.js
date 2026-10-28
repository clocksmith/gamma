'use strict';

// 636. Exclusive Time of Functions (Medium).
// Specification: https://leetcode.com/problems/exclusive-time-of-functions/description/
function solve(n, logs) {
  const result = new Array(n).fill(0);
  const stack = [];
  let previous = 0;
  for (const log of logs) {
    const parts = log.split(':');
    const id = Number(parts[0]); const kind = parts[1]; const time = Number(parts[2]);
    if (kind === 'start') {
      if (stack.length > 0) result[stack[stack.length - 1]] += time - previous;
      stack.push(id);
      previous = time;
    } else {
      const finished = stack.pop();
      result[finished] += time - previous + 1;
      previous = time + 1;
    }
  }
  return result;
}
const exclusiveTime = solve;
class Solution { exclusiveTime(n, logs) { return solve(n, logs); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, exclusiveTime };
