'use strict';

// 1463. Cherry Pickup II: two-robot row DP; O(rows*columns^2) time and O(columns^2) space. Inputs are preserved.

function solve(grid) {
  const columns = grid[0].length;
  let following = Array.from({ length: columns }, () => Array(columns).fill(0));
  for (let row = grid.length - 1; row >= 0; row -= 1) {
    const current = Array.from({ length: columns }, () => Array(columns).fill(0));
    for (let first = 0; first < columns; first += 1) {
      for (let second = 0; second < columns; second += 1) {
        let best = 0;
        for (let nextFirst = Math.max(0, first - 1); nextFirst < Math.min(columns, first + 2); nextFirst += 1) {
          for (let nextSecond = Math.max(0, second - 1); nextSecond < Math.min(columns, second + 2); nextSecond += 1) {
            best = Math.max(best, following[nextFirst][nextSecond]);
          }
        }
        current[first][second] = grid[row][first] + (first === second ? 0 : grid[row][second]) + best;
      }
    }
    following = current;
  }
  return following[0][columns - 1];
}

const cherryPickup = solve;
class Solution {
  cherryPickup(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, cherryPickup };
