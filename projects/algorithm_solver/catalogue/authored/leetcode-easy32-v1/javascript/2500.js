'use strict';

// 2500. Delete Greatest Value in Each Row (Easy).
// Specification: https://leetcode.com/problems/delete-greatest-value-in-each-row/description/
// O(rows * columns * log(columns)) time, O(rows * columns) space.
// Sort copies so the caller's matrix and row identities remain unchanged.
function solve(grid) {
  const rows = grid.map(row => row.slice().sort((left, right) => left - right));
  let result = 0;
  for (let column = 0; column < rows[0].length; column++) {
    let greatest = 0;
    for (const row of rows) greatest = Math.max(greatest, row[column]);
    result += greatest;
  }
  return result;
}

const deleteGreatestValue = solve;
class Solution {
  deleteGreatestValue(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, deleteGreatestValue };
