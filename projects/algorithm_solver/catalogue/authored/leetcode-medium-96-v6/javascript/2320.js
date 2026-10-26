'use strict';

// 2320. Count Number of Ways to Place Houses: count nonadjacent placements on one side and combine the independent sides.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(n) {
  const modulus = 1000000007;
  let previous = 1;
  let current = 1;
  for (let index = 0; index < n; index += 1) {
    [previous, current] = [current, (previous + current) % modulus];
  }
  return Number(BigInt(current) * BigInt(current) % 1000000007n);
}

const countHousePlacements = solve;
class Solution {
  countHousePlacements(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countHousePlacements };
