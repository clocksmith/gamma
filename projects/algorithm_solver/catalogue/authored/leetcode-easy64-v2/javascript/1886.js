'use strict';

// 1886. Determine Whether Matrix Can Be Obtained By Rotation (Easy).
// Specification: https://leetcode.com/problems/determine-whether-matrix-can-be-obtained-by-rotation/description/
// O(n^2) time, O(1) space; compare rotations without mutating either matrix.
function solve(mat, target) {
  const size = mat.length;
  let unchanged = true;
  let clockwise = true;
  let halfTurn = true;
  let counterclockwise = true;
  for (let row = 0; row < size; row++) {
    for (let column = 0; column < size; column++) {
      const value = target[row][column];
      unchanged = unchanged && mat[row][column] === value;
      clockwise = clockwise && mat[size - 1 - column][row] === value;
      halfTurn = halfTurn && mat[size - 1 - row][size - 1 - column] === value;
      counterclockwise = counterclockwise && mat[column][size - 1 - row] === value;
    }
  }
  return unchanged || clockwise || halfTurn || counterclockwise;
}

const findRotation = solve;
class Solution {
  findRotation(mat, target) { return solve(mat, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRotation };
