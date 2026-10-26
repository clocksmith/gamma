'use strict';

// 2038. Remove Colored Pieces if Both Neighbors are the Same Color: count the removable interior pieces in each color run.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(colors) {
  let alice = 0;
  let bob = 0;
  for (let index = 1; index + 1 < colors.length; index += 1) {
    if (colors[index - 1] === colors[index] && colors[index] === colors[index + 1]) {
      if (colors[index] === 'A') alice += 1;
      else bob += 1;
    }
  }
  return alice > bob;
}

const winnerOfGame = solve;
class Solution {
  winnerOfGame(colors) { return solve(colors); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, winnerOfGame };
