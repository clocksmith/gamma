'use strict';

// 3799. Word Squares II.
// O(n^4) time and O(n) auxiliary space excluding returned squares; n <= 15 and output is lexicographically ordered.
function solve(words) {
  const ordered = words.slice().sort();
  const answer = [];
  for (const top of ordered) {
    for (const left of ordered) {
      if (left === top || left[0] !== top[0]) continue;
      for (const right of ordered) {
        if (right === top || right === left || right[0] !== top[3]) continue;
        for (const bottom of ordered) {
          if (bottom === top || bottom === left || bottom === right) continue;
          if (bottom[0] === left[3] && bottom[3] === right[3]) answer.push([top, left, right, bottom]);
        }
      }
    }
  }
  return answer;
}

const wordSquares = solve;
class Solution {
  wordSquares(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, wordSquares };
