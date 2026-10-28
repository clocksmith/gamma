'use strict';

// 1861. Rotating the Box (Medium).
// Specification: https://leetcode.com/problems/rotating-the-box/description/
function settleRow(row) {
  const result = row.slice();
  let write = result.length - 1;
  for (let i = result.length - 1; i >= 0; i--) {
    if (result[i] === '*') write = i - 1;
    else if (result[i] === '#') { result[i] = '.'; result[write] = '#'; write--; }
  }
  return result;
}
function solve(box) {
  const settled = box.map(settleRow);
  const rows = settled.length; const cols = settled[0].length;
  const result = [];
  for (let c = 0; c < cols; c++) {
    const row = [];
    for (let r = rows - 1; r >= 0; r--) row.push(settled[r][c]);
    result.push(row);
  }
  return result;
}
const rotateTheBox = solve;
class Solution { rotateTheBox(box) { return solve(box); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rotateTheBox };
