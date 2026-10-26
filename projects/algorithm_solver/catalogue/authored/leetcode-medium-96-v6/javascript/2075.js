'use strict';

// 2075. Decode the Slanted Ciphertext: read the stored rectangle along diagonals and discard only trailing spaces.
// O(L) time and O(L) auxiliary and result space for L encoded characters; inputs are read-only.
function solve(encodedText, rows) {
  const columns = Math.floor(encodedText.length / rows);
  const decoded = [];
  for (let start = 0; start < columns; start += 1) {
    let row = 0;
    let column = start;
    while (row < rows && column < columns) {
      decoded.push(encodedText[row * columns + column]);
      row += 1;
      column += 1;
    }
  }
  return decoded.join('').replace(/ +$/, '');
}

const decodeCiphertext = solve;
class Solution {
  decodeCiphertext(encodedText, rows) { return solve(encodedText, rows); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, decodeCiphertext };
