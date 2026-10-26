'use strict';

// 2027. Minimum Moves to Convert String (Easy).
// Specification: https://leetcode.com/problems/minimum-moves-to-convert-string/description/
// O(n) time, O(1) space; greedily cover the leftmost X with a length-three operation.
function solve(s) {
  let moves = 0;
  let index = 0;
  while (index < s.length) {
    if (s[index] === 'X') {
      moves++;
      index += 3;
    } else {
      index++;
    }
  }
  return moves;
}

const minimumMoves = solve;
class Solution {
  minimumMoves(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumMoves };
