'use strict';

// 688. Knight Probability in Chessboard.

function solve(n, k, row, column) {
  const moves = [[1, 2], [1, -2], [-1, 2], [-1, -2], [2, 1], [2, -1], [-2, 1], [-2, -1]];
  let probability = Array.from({length: n}, () => Array(n).fill(0));
  probability[row][column] = 1;
  for (let step = 0; step < k; step += 1) {
    const next = Array.from({length: n}, () => Array(n).fill(0));
    for (let r = 0; r < n; r += 1) for (let c = 0; c < n; c += 1) {
      if (probability[r][c] === 0) continue;
      const share = probability[r][c] / 8;
      for (const [dr, dc] of moves) {
        const nr = r + dr, nc = c + dc;
        if (nr >= 0 && nr < n && nc >= 0 && nc < n) next[nr][nc] += share;
      }
    }
    probability = next;
  }
  return probability.reduce((sum, values) => sum + values.reduce((a, b) => a + b, 0), 0);
}

const knightProbability = solve;
class Solution {
  knightProbability(n, k, row, column) { return solve(n, k, row, column); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, knightProbability };
