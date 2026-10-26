'use strict';

// 1301. Number of Paths with Max Score: reverse grid dynamic programming; O(rows*columns) time and space. Board contents are preserved.

function solve(board) {
  const modulus = 1000000007;
  const rows = board.length;
  const columns = board[0].length;
  const score = Array.from({ length: rows }, () => Array(columns).fill(-1));
  const ways = Array.from({ length: rows }, () => Array(columns).fill(0));
  score[rows - 1][columns - 1] = 0;
  ways[rows - 1][columns - 1] = 1;
  for (let row = rows - 1; row >= 0; row -= 1) {
    for (let column = columns - 1; column >= 0; column -= 1) {
      if (board[row][column] === 'X' || (row === rows - 1 && column === columns - 1)) continue;
      let best = -1;
      let count = 0;
      for (const [nr, nc] of [[row + 1, column], [row, column + 1], [row + 1, column + 1]]) {
        if (nr >= rows || nc >= columns || score[nr][nc] < 0) continue;
        if (score[nr][nc] > best) {
          best = score[nr][nc];
          count = ways[nr][nc];
        } else if (score[nr][nc] === best) count = (count + ways[nr][nc]) % modulus;
      }
      if (best >= 0) {
        const value = board[row][column] === 'E' ? 0 : Number(board[row][column]);
        score[row][column] = best + value;
        ways[row][column] = count;
      }
    }
  }
  return score[0][0] >= 0 ? [score[0][0], ways[0][0]] : [0, 0];
}

const pathsWithMaxScore = solve;
class Solution {
  pathsWithMaxScore(board) { return solve(board); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, pathsWithMaxScore };
