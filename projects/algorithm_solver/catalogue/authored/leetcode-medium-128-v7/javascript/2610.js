'use strict';

// 2610. Convert an Array Into a 2D Array With Conditions: place the jth occurrence of a value in row j.
// O(n) expected time and O(n) auxiliary space including the result; inputs are read-only.
function solve(nums) {
  const counts = new Map();
  const rows = [];
  for (const value of nums) {
    const row = counts.get(value) || 0;
    if (row === rows.length) rows.push([]);
    rows[row].push(value);
    counts.set(value, row + 1);
  }
  return rows;
}

const findMatrix = solve;
class Solution {
  findMatrix(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMatrix };
