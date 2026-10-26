'use strict';

// 2139. Minimum Moves to Reach Target Score: work backward by halving whenever allowed and removing an odd excess first.
// O(log target) time and O(1) auxiliary space; inputs are read-only.
function solve(target, maxDoubles) {
  let current = target;
  let doubles = maxDoubles;
  let moves = 0;
  while (current > 1 && doubles > 0) {
    if (current % 2) {
      current -= 1;
      moves += 1;
    }
    current = Math.floor(current / 2);
    doubles -= 1;
    moves += 1;
  }
  return moves + current - 1;
}

const minMoves = solve;
class Solution {
  minMoves(target, maxDoubles) { return solve(target, maxDoubles); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMoves };
