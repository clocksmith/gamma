'use strict';

// 2120. Execution of All Suffix Instructions Staying in a Grid: simulate each bounded instruction suffix until its first out-of-grid move.
// O(m^2) time and O(m) result space for at most 500 instructions; inputs are read-only.
function solve(n, startPos, s) {
  const directions = { L: [0, -1], R: [0, 1], U: [-1, 0], D: [1, 0] };
  const result = new Array(s.length).fill(0);
  for (let start = 0; start < s.length; start += 1) {
    let [row, column] = startPos;
    for (let index = start; index < s.length; index += 1) {
      const [dr, dc] = directions[s[index]];
      row += dr;
      column += dc;
      if (row < 0 || row >= n || column < 0 || column >= n) break;
      result[start] += 1;
    }
  }
  return result;
}

const executeInstructions = solve;
class Solution {
  executeInstructions(n, startPos, s) { return solve(n, startPos, s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, executeInstructions };
