'use strict';

// 1424. Diagonal Traverse II: bucket ragged rows by diagonal and read each bucket bottom-up.
// O(S) time and O(S) auxiliary space, where S is the total number of elements; inputs are read-only.
function solve(nums) {
  const diagonals = [];
  for (let row = 0; row < nums.length; row += 1) {
    for (let col = 0; col < nums[row].length; col += 1) {
      const diagonal = row + col;
      while (diagonals.length <= diagonal) diagonals.push([]);
      diagonals[diagonal].push(nums[row][col]);
    }
  }
  const result = [];
  for (const diagonal of diagonals) {
    for (let index = diagonal.length - 1; index >= 0; index -= 1) result.push(diagonal[index]);
  }
  return result;
}

const findDiagonalOrder = solve;
class Solution {
  findDiagonalOrder(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDiagonalOrder };
