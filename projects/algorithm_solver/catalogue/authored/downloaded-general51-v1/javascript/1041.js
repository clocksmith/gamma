'use strict';

// 1041. Robot Bounded In Circle (Easy).
// Specification: https://leetcode.com/problems/robot-bounded-in-circle/description/
function solve(instructions) {
  let x = 0; let y = 0; let direction = 0;
  const moves = [[0, 1], [1, 0], [0, -1], [-1, 0]];
  for (const ch of instructions) {
    if (ch === 'G') { x += moves[direction][0]; y += moves[direction][1]; }
    else if (ch === 'L') direction = (direction + 3) % 4;
    else direction = (direction + 1) % 4;
  }
  return (x === 0 && y === 0) || direction !== 0;
}
const isRobotBounded = solve;
class Solution { isRobotBounded(instructions) { return solve(instructions); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isRobotBounded };
