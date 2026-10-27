'use strict';

// 636. Exclusive Time of Functions.

function solve(n, logs) {
  const answer = Array(n).fill(0), stack = [];
  let previous = 0;
  for (const log of logs) {
    const parts = log.split(':'), id = Number(parts[0]), event = parts[1], timestamp = Number(parts[2]);
    if (event === 'start') {
      if (stack.length > 0) answer[stack[stack.length - 1]] += timestamp - previous;
      stack.push(id); previous = timestamp;
    } else { answer[stack.pop()] += timestamp - previous + 1; previous = timestamp + 1; }
  }
  return answer;
}

const exclusiveTime = solve;
class Solution {
  exclusiveTime(n, logs) { return solve(n, logs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, exclusiveTime };
