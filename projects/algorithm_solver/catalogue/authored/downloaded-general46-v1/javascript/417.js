'use strict';

// 417. Pacific Atlantic Water Flow (Medium).
// Specification: https://leetcode.com/problems/pacific-atlantic-water-flow/description/
function solve(heights) {
  const rows = heights.length; const cols = heights[0].length;
  function reachableFrom(ocean) {
    const seen = new Set();
    const stack = [];
    for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { if ((ocean === 'pacific' && (r === 0 || c === 0)) || (ocean === 'atlantic' && (r === rows - 1 || c === cols - 1))) { seen.add(r + ',' + c); stack.push([r, c]); } } }
    const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
    while (stack.length > 0) {
      const [r, c] = stack.pop();
      for (const [dr, dc] of directions) {
        const nr = r + dr; const nc = c + dc;
        if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
        if (seen.has(nr + ',' + nc)) continue;
        if (heights[nr][nc] < heights[r][c]) continue;
        seen.add(nr + ',' + nc); stack.push([nr, nc]);
      }
    }
    return seen;
  }
  const pacific = reachableFrom('pacific');
  const atlantic = reachableFrom('atlantic');
  const result = [];
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { if (pacific.has(r + ',' + c) && atlantic.has(r + ',' + c)) result.push([r, c]); } }
  return result;
}
const pacificAtlantic = solve;
class Solution { pacificAtlantic(heights) { return solve(heights); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, pacificAtlantic };
