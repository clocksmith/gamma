'use strict';

// 2018. Check if Word Can Be Placed In Crossword: match complete horizontal or vertical slots in either reading direction.
// O(rows * columns) time and O(1) auxiliary space; inputs are read-only.
function solve(board, word) {
  const rows = board.length;
  const columns = board[0].length;
  const length = word.length;
  function matches(row, column, dr, dc) {
    let forward = true;
    let backward = true;
    for (let index = 0; index < length; index += 1) {
      const letter = board[row + index * dr][column + index * dc];
      if (letter !== ' ' && letter !== word[index]) forward = false;
      if (letter !== ' ' && letter !== word[length - 1 - index]) backward = false;
      if (!forward && !backward) return false;
    }
    return forward || backward;
  }
  for (let row = 0; row < rows; row += 1) {
    let start = 0;
    for (let column = 0; column <= columns; column += 1) {
      if (column === columns || board[row][column] === '#') {
        if (column - start === length && matches(row, start, 0, 1)) return true;
        start = column + 1;
      }
    }
  }
  for (let column = 0; column < columns; column += 1) {
    let start = 0;
    for (let row = 0; row <= rows; row += 1) {
      if (row === rows || board[row][column] === '#') {
        if (row - start === length && matches(start, column, 1, 0)) return true;
        start = row + 1;
      }
    }
  }
  return false;
}

const placeWordInCrossword = solve;
class Solution {
  placeWordInCrossword(board, word) { return solve(board, word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, placeWordInCrossword };
