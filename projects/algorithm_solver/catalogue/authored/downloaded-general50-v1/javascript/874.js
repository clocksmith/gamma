'use strict';

// 874. Walking Robot Simulation (Medium).
// Specification: https://leetcode.com/problems/walking-robot-simulation/description/
function solve(commands, obstacles) {
  const blocked = new Set(obstacles.map(([x, y]) => x + ',' + y));
  const dirs = [[0, 1], [1, 0], [0, -1], [-1, 0]];
  let dir = 0; let x = 0; let y = 0; let best = 0;
  for (const cmd of commands) {
    if (cmd === -2) dir = (dir + 3) % 4;
    else if (cmd === -1) dir = (dir + 1) % 4;
    else {
      for (let step = 0; step < cmd; step++) {
        const nx = x + dirs[dir][0]; const ny = y + dirs[dir][1];
        if (blocked.has(nx + ',' + ny)) break;
        x = nx; y = ny;
        best = Math.max(best, x * x + y * y);
      }
    }
  }
  return best;
}
const robotSim = solve;
class Solution { robotSim(commands, obstacles) { return solve(commands, obstacles); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, robotSim };
