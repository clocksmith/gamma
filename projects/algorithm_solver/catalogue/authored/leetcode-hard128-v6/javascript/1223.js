'use strict';

// 1223. Dice Roll Simulation.
// Track the final face and its run length; O(n * sum(rollMax)) time and O(sum(rollMax)) space. Inputs are preserved.

function solve(n, rollMax) {
  const modulus = 1000000007;
  let runs = rollMax.map(limit => Array(limit + 1).fill(0));
  for (let face = 0; face < 6; face += 1) runs[face][1] = 1;
  for (let step = 1; step < n; step += 1) {
    const totals = runs.map(row => row.reduce((sum, value) => (sum + value) % modulus, 0));
    const total = totals.reduce((sum, value) => (sum + value) % modulus, 0);
    const following = rollMax.map(limit => Array(limit + 1).fill(0));
    for (let face = 0; face < 6; face += 1) {
      following[face][1] = (total - totals[face] + modulus) % modulus;
      for (let length = 2; length <= rollMax[face]; length += 1) following[face][length] = runs[face][length - 1];
    }
    runs = following;
  }
  return runs.reduce((sum, row) => row.reduce((value, count) => (value + count) % modulus, sum), 0);
}

const dieSimulator = solve;
class Solution {
  dieSimulator(n, rollMax) { return solve(n, rollMax); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, dieSimulator };
