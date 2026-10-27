'use strict';

// 417. Pacific Atlantic Water Flow. Reverse uphill reachability from both ocean borders.

function solve(heights) {
  const rows = heights.length, cols = heights[0].length;
  function reach(starts) {
    const seen = new Set(starts.map(([r, c]) => r * cols + c));
    const stack = Array.from(seen);
    while (stack.length > 0) {
      const cell = stack.pop(), r = Math.floor(cell / cols), c = cell % cols;
      for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nr = r + dr, nc = c + dc, next = nr * cols + nc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !seen.has(next) && heights[nr][nc] >= heights[r][c]) {
          seen.add(next); stack.push(next);
        }
      }
    }
    return seen;
  }
  const p = [], a = [];
  for (let c = 0; c < cols; c += 1) { p.push([0, c]); a.push([rows - 1, c]); }
  for (let r = 0; r < rows; r += 1) { p.push([r, 0]); a.push([r, cols - 1]); }
  const pacific = reach(p), atlantic = reach(a), answer = [];
  for (let r = 0; r < rows; r += 1) for (let c = 0; c < cols; c += 1) {
    if (pacific.has(r * cols + c) && atlantic.has(r * cols + c)) answer.push([r, c]);
  }
  return answer;
}

const pacificAtlantic = solve;
class Solution {
  pacificAtlantic(heights) { return solve(heights); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, pacificAtlantic };
