'use strict';

// 293. Flip Game (Easy).
// Specification: https://leetcode.com/problems/flip-game/description/
// O(n^2) worst-case time and result space; emit moves in increasing flipped-index order.
function solve(currentState) {
  const result = [];
  for (let index = 0; index + 1 < currentState.length; index++) {
    if (currentState[index] === '+' && currentState[index + 1] === '+') {
      result.push(currentState.slice(0, index) + '--' + currentState.slice(index + 2));
    }
  }
  return result;
}

const generatePossibleNextMoves = solve;
class Solution {
  generatePossibleNextMoves(currentState) { return solve(currentState); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, generatePossibleNextMoves };
