'use strict';

// 3797. Count Routes to Climb a Rectangular Grid.
// O(rows * columns) time and O(columns) space; vertical radius is d-1 and each row permits zero or one horizontal move.
function solve(grid, d) {
  const modulus = 1000000007;
  const columns = grid[0].length;
  function windowSums(values, radius) {
    const prefix = new Float64Array(columns + 1);
    for (let index = 0; index < columns; index += 1) prefix[index + 1] = (prefix[index] + values[index]) % modulus;
    const result = new Float64Array(columns);
    for (let index = 0; index < columns; index += 1) {
      result[index] = (prefix[Math.min(columns, index + radius + 1)] - prefix[Math.max(0, index - radius)] + modulus) % modulus;
    }
    return result;
  }
  let previous = null;
  for (let row = grid.length - 1; row >= 0; row -= 1) {
    const entering = previous === null ? new Float64Array(columns).fill(1) : windowSums(previous, d - 1);
    for (let column = 0; column < columns; column += 1) if (grid[row][column] === '#') entering[column] = 0;
    previous = windowSums(entering, d);
    for (let column = 0; column < columns; column += 1) if (grid[row][column] === '#') previous[column] = 0;
  }
  let answer = 0;
  for (const value of previous) answer = (answer + value) % modulus;
  return answer;
}

const numberOfRoutes = solve;
class Solution {
  numberOfRoutes(grid, d) { return solve(grid, d); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfRoutes };
