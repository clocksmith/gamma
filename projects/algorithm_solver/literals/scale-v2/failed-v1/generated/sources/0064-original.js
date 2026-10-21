/* 64. Minimum Path Sum */
function minPathSum(grid) {
  const rowCount = grid.length,
    columnCount = grid[0].length;
  const pathCosts = Array(columnCount).fill(Infinity);
  pathCosts[0] = 0;
  for (let rowIndex = 0; rowIndex < rowCount; rowIndex++) {
    for (let columnIndex = 0; columnIndex < columnCount; columnIndex++) {
      pathCosts[columnIndex] = grid[rowIndex][columnIndex] + Math.min(pathCosts[columnIndex], columnIndex ? pathCosts[columnIndex - 1] : Infinity);
    }
  }
  return pathCosts[columnCount - 1];
}
