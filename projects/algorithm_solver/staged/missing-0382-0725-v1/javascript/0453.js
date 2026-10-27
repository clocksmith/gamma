'use strict';

// 453. Minimum Moves to Equal Array Elements. Incrementing n-1 entries is equivalent to decrementing one relative value.

function solve(nums) {
  let minimum = Infinity, total = 0;
  for (const value of nums) { minimum = Math.min(minimum, value); total += value; }
  return total - minimum * nums.length;
}

const minMoves = solve;
class Solution {
  minMoves(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMoves };
