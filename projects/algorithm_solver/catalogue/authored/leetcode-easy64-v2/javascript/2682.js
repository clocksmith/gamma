'use strict';

// 2682. Find the Losers of the Circular Game (Easy).
// Specification: https://leetcode.com/problems/find-the-losers-of-the-circular-game/description/
// O(n) time, O(n) space; stop on the first repeated recipient.
function solve(n, k) {
  const visited = new Array(n).fill(false);
  let current = 0;
  let turn = 1;
  while (!visited[current]) {
    visited[current] = true;
    current = (current + turn * k) % n;
    turn++;
  }
  const result = [];
  for (let index = 0; index < n; index++) {
    if (!visited[index]) result.push(index + 1);
  }
  return result;
}

const circularGameLosers = solve;
class Solution {
  circularGameLosers(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, circularGameLosers };
