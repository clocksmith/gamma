"use strict";
// Hack2Hire 69a357a36e73e4abccc9bf9c (Matrix Transformation with Commands) over an INFERRED spec; qualification unknown.

function solve(matrix, commands) {
  const n = matrix.length;
  const order = [];
  for (let i = 0; i < n; i++) order.push(i);
  const flipped = new Array(n).fill(false);
  for (const command of commands) {
    const parts = command.split(" ");
    if (parts[0] === "reverseRow") {
      const row = order[Number(parts[1])];
      flipped[row] = !flipped[row];
    } else {
      const a = Number(parts[1]), b = Number(parts[2]);
      const t = order[a];
      order[a] = order[b];
      order[b] = t;
    }
  }
  return order.map((row) => (flipped[row] ? matrix[row].slice().reverse() : matrix[row].slice()));
}

function transformMatrix(matrix, commands) { return solve(matrix, commands); }

module.exports = solve;
module.exports.transformMatrix = transformMatrix;
