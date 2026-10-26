'use strict';

// 2766. Relocate Marbles: track occupied positions since every move relocates all marbles at its source.
// O(n + m + u log u) expected time and O(u) auxiliary space for u distinct occupied positions; inputs are read-only.
function solve(nums, moveFrom, moveTo) {
  const occupied = new Set(nums);
  for (let index = 0; index < moveFrom.length; index += 1) {
    occupied.delete(moveFrom[index]);
    occupied.add(moveTo[index]);
  }
  return Array.from(occupied).sort((left, right) => left - right);
}

const relocateMarbles = solve;
class Solution {
  relocateMarbles(nums, moveFrom, moveTo) { return solve(nums, moveFrom, moveTo); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, relocateMarbles };
