'use strict';
// 212. Word Search II.
function solve(board, words) {
  const root = {};
  for (const word of words) {
    let node = root;
    for (const char of word) { if (!(char in node)) node[char] = {}; node = node[char]; }
    node.$ = word;
  }
  const result = []; const rows = board.length; const columns = board[0].length;
  function visit(row, column, node) {
    const char = board[row][column];
    if (!(char in node)) return;
    const following = node[char];
    if ('$' in following) { result.push(following.$); delete following.$; }
    board[row][column] = '#';
    for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nr = row + dr; const nc = column + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < columns && board[nr][nc] !== '#') visit(nr, nc, following);
    }
    board[row][column] = char;
    if (Object.keys(following).length === 0) delete node[char];
  }
  for (let row = 0; row < rows; row += 1) for (let column = 0; column < columns; column += 1) visit(row, column, root);
  return result;
}
const findWords = solve;
class Solution { findWords(board, words) { return solve(board, words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findWords };
