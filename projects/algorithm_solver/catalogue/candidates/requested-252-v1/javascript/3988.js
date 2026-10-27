/**
 * 3988. Create Grid With Exactly K Paths I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/create-grid-with-exactly-k-paths-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3988.Create%20Grid%20With%20Exactly%20K%20Paths%20I/README_EN.md
 * Complexity: O(m*n) time and output space.
 * Constructs 2-by-k path-count gadget or a 3-by-3 four-path gadget; a single exit corridor preserves the count. Complete for stated 1<=k<=4. Native method unconfirmed.
 */

function solve(m, n, k) {
  const grid = Array.from({length: m}, () => Array(n).fill('#'));
  let height, width;
  if (k === 1) { height = width = 1; grid[0][0] = '.'; }
  else if (m >= 2 && n >= k) { height = 2; width = k; }
  else if (n >= 2 && m >= k) { height = k; width = 2; }
  else if (k === 4 && m >= 3 && n >= 3) { height = width = 3; }
  else return [];
  if (k !== 1) for (let i = 0; i < height; i++) for (let j = 0; j < width; j++) {
    if (height === 3 && width === 3 && ((i === 0 && j === 2) || (i === 2 && j === 0))) continue;
    grid[i][j] = '.';
  }
  for (let i = height - 1; i < m; i++) grid[i][width - 1] = '.';
  for (let j = width - 1; j < n; j++) grid[m - 1][j] = '.';
  return grid.map(row => row.join(''));
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
