'use strict';

// 533. Lonely Pixel II.

function solve(picture, target) {
  const rows = new Map(), columns = Array(picture[0].length).fill(0);
  for (const row of picture) {
    const text = row.join(''); rows.set(text, (rows.get(text) || 0) + 1);
    for (let c = 0; c < row.length; c += 1) if (row[c] === 'B') columns[c] += 1;
  }
  let answer = 0;
  for (const [row, copies] of rows) {
    let black = 0;
    for (const char of row) if (char === 'B') black += 1;
    if (copies === target && black === target) {
      for (let c = 0; c < row.length; c += 1) if (row[c] === 'B' && columns[c] === target) answer += target;
    }
  }
  return answer;
}

const findBlackPixel = solve;
class Solution {
  findBlackPixel(picture, target) { return solve(picture, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findBlackPixel };
