'use strict';

// 2147. Number of Ways to Divide a Long Corridor. Multiply the divider gaps between consecutive seat pairs; O(n) time and O(1) space. Inputs are preserved.

function solve(corridor) {
  const modulus = 1000000007;
  let seats = 0;
  let previous = -1;
  let ways = 1;
  for (let index = 0; index < corridor.length; index += 1) {
    if (corridor[index] !== 'S') continue;
    seats += 1;
    if (seats > 2 && seats % 2 === 1) ways = ways * (index - previous) % modulus;
    if (seats % 2 === 0) previous = index;
  }
  return seats > 0 && seats % 2 === 0 ? ways : 0;
}

const numberOfWays = solve;
class Solution {
  numberOfWays(corridor) { return solve(corridor); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfWays };
