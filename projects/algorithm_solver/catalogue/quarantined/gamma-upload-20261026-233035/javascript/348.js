'use strict';
// 348. Design Tic-Tac-Toe.
class TicTacToe {
  constructor(n) {
    this.size = n; this.rows = Array(n).fill(0); this.columns = Array(n).fill(0);
    this.diagonal = 0; this.antiDiagonal = 0;
  }
  move(row, col, player) {
    const value = player === 1 ? 1 : -1;
    this.rows[row] += value; this.columns[col] += value;
    if (row === col) this.diagonal += value;
    if (row + col === this.size - 1) this.antiDiagonal += value;
    return Math.abs(this.rows[row]) === this.size || Math.abs(this.columns[col]) === this.size
      || Math.abs(this.diagonal) === this.size || Math.abs(this.antiDiagonal) === this.size ? player : 0;
  }
}
function solve(n, moves) {
  const game = new TicTacToe(n);
  return moves.map(move => game.move(...move));
}
if (typeof module !== 'undefined') module.exports = { solve, TicTacToe };
