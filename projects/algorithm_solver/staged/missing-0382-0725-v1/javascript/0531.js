'use strict';

// 531. Lonely Pixel I.

function solve(picture) {
  const rows = picture.length, cols = picture[0].length, rowCounts = Array(rows).fill(0), colCounts = Array(cols).fill(0);
  for (let r = 0; r < rows; r += 1) for (let c = 0; c < cols; c += 1) if (picture[r][c] === 'B') { rowCounts[r] += 1; colCounts[c] += 1; }
  let answer = 0;
  for (let r = 0; r < rows; r += 1) for (let c = 0; c < cols; c += 1) if (picture[r][c] === 'B' && rowCounts[r] === 1 && colCounts[c] === 1) answer += 1;
  return answer;
}

const findLonelyPixel = solve;
class Solution {
  findLonelyPixel(picture) { return solve(picture); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLonelyPixel };
