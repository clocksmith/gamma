"use strict";
// Hack2Hire 6795a8a1010c9ed2f849b1fd (Find Word Path) over an INFERRED spec; qualification unknown.

function solve(word) {
  const out = [];
  let row = 0, col = 0;
  for (let i = 0; i < word.length; i++) {
    const index = word.charCodeAt(i) - 97, targetRow = Math.floor(index / 5), targetCol = index % 5;
    // up and left before down and right keeps the cursor on the board around 'z'
    if (targetRow < row) out.push("U".repeat(row - targetRow));
    if (targetCol < col) out.push("L".repeat(col - targetCol));
    if (targetRow > row) out.push("D".repeat(targetRow - row));
    if (targetCol > col) out.push("R".repeat(targetCol - col));
    out.push("!");
    row = targetRow; col = targetCol;
  }
  return out.join("");
}

function findWordPath(word) { return solve(word); }

module.exports = solve;
module.exports.findWordPath = findWordPath;
