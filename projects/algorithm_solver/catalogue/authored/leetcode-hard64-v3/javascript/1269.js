'use strict';

// 1269. Number of Ways to Stay in the Same Place After Some Steps: bounded-position dynamic programming; O(steps*min(arrLen, steps)) time and O(min(arrLen, steps)) space.

function solve(steps, arrLen) {
  const modulus = 1000000007;
  const width = Math.min(arrLen, Math.floor(steps / 2) + 1);
  let ways = Array(width).fill(0);
  ways[0] = 1;
  for (let step = 0; step < steps; step += 1) {
    const following = Array(width).fill(0);
    for (let position = 0; position < width; position += 1) {
      following[position] = (following[position] + ways[position]) % modulus;
      if (position > 0) following[position - 1] = (following[position - 1] + ways[position]) % modulus;
      if (position + 1 < width) following[position + 1] = (following[position + 1] + ways[position]) % modulus;
    }
    ways = following;
  }
  return ways[0];
}

const numWays = solve;
class Solution {
  numWays(steps, arrLen) { return solve(steps, arrLen); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numWays };
