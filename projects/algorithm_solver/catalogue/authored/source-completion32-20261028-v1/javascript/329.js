// 329 — Longest Increasing Path in a Matrix. Original implementation; authored candidate, not independently qualified.
function solve(matrix) {
  if (!matrix.length || !matrix[0].length) return 0;
  const rows = matrix.length, cols = matrix[0].length, dirs = [[1,0],[-1,0],[0,1],[0,-1]];
  const degree = Array.from({length: rows}, () => Array(cols).fill(0)), queue = [];
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    for (const [dr, dc] of dirs) if (r + dr >= 0 && r + dr < rows && c + dc >= 0 && c + dc < cols && matrix[r + dr][c + dc] > matrix[r][c]) degree[r][c]++;
    if (!degree[r][c]) queue.push([r, c]);
  }
  let head = 0, layers = 0;
  while (head < queue.length) {
    const end = queue.length; layers++;
    while (head < end) {
      const [r,c] = queue[head++];
      for (const [dr,dc] of dirs) {
        const nr = r + dr, nc = c + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && matrix[nr][nc] < matrix[r][c] && --degree[nr][nc] === 0) queue.push([nr,nc]);
      }
    }
  }
  return layers;
}

module.exports = { solve, longestIncreasingPath: solve };
