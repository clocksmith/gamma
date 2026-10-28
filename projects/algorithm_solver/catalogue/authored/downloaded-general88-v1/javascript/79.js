'use strict';

// 79. Word Search (Medium).
// Specification: https://leetcode.com/problems/word-search/description/
function solve(board, word) {
  const rows = board.length; const cols = board[0].length;
  function dfs(r, c, index) {
    if (index === word.length) return true;
    if (r < 0 || r >= rows || c < 0 || c >= cols || board[r][c] !== word[index]) return false;
    const saved = board[r][c];
    board[r][c] = '#';
    const found = dfs(r + 1, c, index + 1) || dfs(r - 1, c, index + 1) || dfs(r, c + 1, index + 1) || dfs(r, c - 1, index + 1);
    board[r][c] = saved;
    return found;
  }
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { if (dfs(r, c, 0)) return true; } }
  return false;
}
const exist = solve;
class Solution { exist(board, word) { return solve(board, word); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, exist };
