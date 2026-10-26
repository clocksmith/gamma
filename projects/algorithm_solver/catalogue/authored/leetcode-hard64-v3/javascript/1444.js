'use strict';

// 1444. Number of Ways of Cutting a Pizza: suffix apple counts and cut DP; O(k*rows*columns*(rows+columns)) time and O(rows*columns) space.

function solve(pizza, k) {
  const modulus = 1000000007;
  const rows = pizza.length;
  const columns = pizza[0].length;
  const apples = Array.from({ length: rows + 1 }, () => Array(columns + 1).fill(0));
  for (let row = rows - 1; row >= 0; row -= 1) {
    for (let column = columns - 1; column >= 0; column -= 1) {
      apples[row][column] = (pizza[row][column] === 'A' ? 1 : 0) + apples[row + 1][column]
        + apples[row][column + 1] - apples[row + 1][column + 1];
    }
  }
  let previous = Array.from({ length: rows }, (_, row) =>
    Array.from({ length: columns }, (_, column) => apples[row][column] > 0 ? 1 : 0));
  for (let pieces = 2; pieces <= k; pieces += 1) {
    const current = Array.from({ length: rows }, () => Array(columns).fill(0));
    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        for (let cut = row + 1; cut < rows; cut += 1) {
          if (apples[row][column] > apples[cut][column]) current[row][column] = (current[row][column] + previous[cut][column]) % modulus;
        }
        for (let cut = column + 1; cut < columns; cut += 1) {
          if (apples[row][column] > apples[row][cut]) current[row][column] = (current[row][column] + previous[row][cut]) % modulus;
        }
      }
    }
    previous = current;
  }
  return previous[0][0];
}

const ways = solve;
class Solution {
  ways(pizza, k) { return solve(pizza, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, ways };
