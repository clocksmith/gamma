'use strict';
// 37. Sudoku Solver.
function solve(board) {
  const rows = Array.from({ length: 9 }, () => new Set());
  const columns = Array.from({ length: 9 }, () => new Set());
  const boxes = Array.from({ length: 9 }, () => new Set());
  const empty = [];
  for (let row = 0; row < 9; row += 1) for (let column = 0; column < 9; column += 1) {
    const value = board[row][column];
    if (value === '.') empty.push([row, column]);
    else { rows[row].add(value); columns[column].add(value); boxes[Math.floor(row / 3) * 3 + Math.floor(column / 3)].add(value); }
  }
  function visit(index) {
    if (index === empty.length) return true;
    let best = index;
    let bestOptions = null;
    for (let candidate = index; candidate < empty.length; candidate += 1) {
      const [row, column] = empty[candidate];
      const box = Math.floor(row / 3) * 3 + Math.floor(column / 3);
      const options = [];
      for (let digit = 1; digit <= 9; digit += 1) {
        const value = String(digit);
        if (!rows[row].has(value) && !columns[column].has(value) && !boxes[box].has(value)) options.push(value);
      }
      if (bestOptions === null || options.length < bestOptions.length) { best = candidate; bestOptions = options; }
      if (bestOptions.length <= 1) break;
    }
    [empty[index], empty[best]] = [empty[best], empty[index]];
    const [row, column] = empty[index];
    const box = Math.floor(row / 3) * 3 + Math.floor(column / 3);
    for (const value of bestOptions) {
      board[row][column] = value;
      rows[row].add(value); columns[column].add(value); boxes[box].add(value);
      if (visit(index + 1)) return true;
      rows[row].delete(value); columns[column].delete(value); boxes[box].delete(value);
    }
    board[row][column] = '.';
    [empty[index], empty[best]] = [empty[best], empty[index]];
    return false;
  }
  visit(0);
}
const solveSudoku = solve;
class Solution { solveSudoku(board) { solve(board); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, solveSudoku };
