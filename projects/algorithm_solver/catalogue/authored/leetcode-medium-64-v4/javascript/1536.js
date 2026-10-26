'use strict';

// 1536. Minimum Swaps to Arrange a Binary Grid: move the nearest row with enough trailing zeros into each position.
// O(n^2) time and O(n) auxiliary space; inputs are read-only.
function solve(grid) {
  const size = grid.length;
  const trailing = [];
  for (const values of grid) {
    let count = 0;
    for (let col = size - 1; col >= 0; col -= 1) {
      if (values[col]) break;
      count += 1;
    }
    trailing.push(count);
  }
  let swaps = 0;
  for (let row = 0; row < size; row += 1) {
    const needed = size - row - 1;
    let chosen = row;
    while (chosen < size && trailing[chosen] < needed) chosen += 1;
    if (chosen === size) return -1;
    swaps += chosen - row;
    const value = trailing[chosen];
    while (chosen > row) {
      trailing[chosen] = trailing[chosen - 1];
      chosen -= 1;
    }
    trailing[row] = value;
  }
  return swaps;
}

const minSwaps = solve;
class Solution {
  minSwaps(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSwaps };
