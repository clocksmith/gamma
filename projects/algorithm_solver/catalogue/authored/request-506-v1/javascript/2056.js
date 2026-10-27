/* Original candidate for LeetCode 2056. Contract: https://leetcode.com/problems/number-of-valid-move-combinations-on-chessboard/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(28^n*n*8) upper bound, O(n*28*8) space; n <= 4, at most one queen */
"use strict";

function solve(pieces, positions) {
  const straight = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  const diagonal = [[1, 1], [1, -1], [-1, 1], [-1, -1]];
  const options = [];
  for (let index = 0; index < pieces.length; index++) {
    const [row, column] = positions[index];
    const directions = pieces[index] === 'rook' ? straight
      : pieces[index] === 'bishop' ? diagonal : [...straight, ...diagonal];
    const paths = [Array(8).fill(row * 8 + column)];
    for (const [dr, dc] of directions) {
      for (let steps = 1; steps <= 7; steps++) {
        const endRow = row + dr * steps;
        const endColumn = column + dc * steps;
        if (endRow < 1 || endRow > 8 || endColumn < 1 || endColumn > 8) break;
        paths.push(Array.from({length: 8}, (_, time) => {
          const elapsed = Math.min(time, steps);
          return (row + dr * elapsed) * 8 + column + dc * elapsed;
        }));
      }
    }
    options.push(paths);
  }
  const chosen = [];
  function visit(index) {
    if (index === pieces.length) return 1;
    let count = 0;
    for (const path of options[index]) {
      // Only simultaneous square collisions count; crossing edges is allowed.
      if (!chosen.every(old => path.every((square, time) => square !== old[time]))) continue;
      chosen.push(path);
      count += visit(index + 1);
      chosen.pop();
    }
    return count;
  }
  return visit(0);
}

module.exports = solve;
