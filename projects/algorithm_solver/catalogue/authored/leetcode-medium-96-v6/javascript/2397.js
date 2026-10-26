'use strict';

// 2397. Maximum Rows Covered by Columns: enumerate the bounded column masks and count contained row masks.
// O(mn + (m + n) * 2^n) time and O(m) auxiliary space for n <= 12 columns; inputs are read-only.
function solve(matrix, numSelect) {
  const columns = matrix[0].length;
  const masks = matrix.map(row => {
    let mask = 0;
    for (let column = 0; column < columns; column += 1) {
      if (row[column]) mask |= 1 << column;
    }
    return mask;
  });
  let best = 0;
  for (let selected = 0; selected < (1 << columns); selected += 1) {
    let bits = selected;
    let count = 0;
    while (bits) {
      bits &= bits - 1;
      count += 1;
    }
    if (count !== numSelect) continue;
    let covered = 0;
    for (const mask of masks) if ((mask & selected) === mask) covered += 1;
    best = Math.max(best, covered);
  }
  return best;
}

const maximumRows = solve;
class Solution {
  maximumRows(matrix, numSelect) { return solve(matrix, numSelect); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumRows };
