'use strict';

// 3996. Even Number of Knight Moves.
// Specification: https://leetcode.com/problems/even-number-of-knight-moves/description/
// O(1) time and space; the standard 8x8 knight graph is connected and bipartite. Inputs are preserved.
function solve(start, target) {
  return (start[0] + start[1]) % 2 === (target[0] + target[1]) % 2;
}

if (typeof module !== 'undefined') module.exports = { solve };
