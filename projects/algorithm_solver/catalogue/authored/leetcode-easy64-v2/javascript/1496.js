'use strict';

// 1496. Path Crossing (Easy).
// Specification: https://leetcode.com/problems/path-crossing/description/
// O(n) expected time, O(n) space under the bounded coordinate domain.
function solve(path) {
  let x = 0;
  let y = 0;
  const visited = new Set(['0,0']);
  for (const direction of path) {
    if (direction === 'N') y++;
    else if (direction === 'S') y--;
    else if (direction === 'E') x++;
    else x--;
    const position = `${x},${y}`;
    if (visited.has(position)) return true;
    visited.add(position);
  }
  return false;
}

const isPathCrossing = solve;
class Solution {
  isPathCrossing(path) { return solve(path); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPathCrossing };
