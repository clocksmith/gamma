'use strict';

// 1654. Minimum Jumps to Reach Home (Medium).
// Specification: https://leetcode.com/problems/minimum-jumps-to-reach-home/description/
function solve(forbidden, a, b, x) {
  const blocked = new Set(forbidden);
  const bound = Math.max(x, ...forbidden, 0) + a + b + 100;
  const queue = [[0, false, 0]];
  const visited = new Set(['0,false']);
  while (queue.length > 0) {
    const [pos, backward, steps] = queue.shift();
    if (pos === x) return steps;
    const forward = pos + a;
    if (forward <= bound && !blocked.has(forward) && !visited.has(`${forward},false`)) { visited.add(`${forward},false`); queue.push([forward, false, steps + 1]); }
    if (!backward) {
      const back = pos - b;
      if (back >= 0 && !blocked.has(back) && !visited.has(`${back},true`)) { visited.add(`${back},true`); queue.push([back, true, steps + 1]); }
    }
  }
  return -1;
}
const minimumJumps = solve;
class Solution { minimumJumps(forbidden, a, b, x) { return solve(forbidden, a, b, x); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumJumps };
