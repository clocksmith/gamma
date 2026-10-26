'use strict';

// 2033. Minimum Operations to Make a Uni-Value Grid: check the common residue and minimize distances to a median.
// O(N log N) time and O(N) auxiliary space for N cells; inputs are read-only.
function solve(grid, x) {
  const values = [];
  for (const row of grid) for (const value of row) values.push(value);
  const residue = values[0] % x;
  for (const value of values) if (value % x !== residue) return -1;
  values.sort((left, right) => left - right);
  const median = values[Math.floor(values.length / 2)];
  let operations = 0;
  for (const value of values) operations += Math.abs(value - median) / x;
  return operations;
}

const minOperations = solve;
class Solution {
  minOperations(grid, x) { return solve(grid, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
