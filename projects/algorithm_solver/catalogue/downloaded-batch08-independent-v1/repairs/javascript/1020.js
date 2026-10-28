'use strict';

// 1020. Number of Enclaves (Medium).
// Specification: https://leetcode.com/problems/number-of-enclaves/description/
function solve(grid) {
  const rows=grid.length, cols=grid[0].length;
  const remaining=grid.map(row=>row.slice());
  const stack=[];
  function enqueue(r,c) { if (remaining[r][c]===1) { remaining[r][c]=0; stack.push(r*cols+c); } }
  for (let r=0;r<rows;r++) { enqueue(r,0); enqueue(r,cols-1); }
  for (let c=0;c<cols;c++) { enqueue(0,c); enqueue(rows-1,c); }
  while (stack.length) {
    const position=stack.pop(), r=Math.floor(position/cols), c=position%cols;
    if (r>0) enqueue(r-1,c);
    if (r+1<rows) enqueue(r+1,c);
    if (c>0) enqueue(r,c-1);
    if (c+1<cols) enqueue(r,c+1);
  }
  let total=0;
  for (const row of remaining) for (const value of row) total+=value;
  return total;
}
const numEnclaves = solve;
class Solution { numEnclaves(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numEnclaves };
