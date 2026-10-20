function maxKilledEnemies(grid) {
  if (grid.length === 0 || grid[0].length === 0) return 0;
  const rows = grid.length;
  const columns = grid[0].length;
  const columnCounts = new Int32Array(columns);
  let best = 0;

  for (let row = 0; row < rows; row++) {
    let rowCount = 0;
    for (let column = 0; column < columns; column++) {
      if (column === 0 || grid[row][column - 1] === 'W') {
        rowCount = 0;
        for (let scan = column; scan < columns && grid[row][scan] !== 'W'; scan++) {
          if (grid[row][scan] === 'E') rowCount++;
        }
      }
      if (row === 0 || grid[row - 1][column] === 'W') {
        columnCounts[column] = 0;
        for (let scan = row; scan < rows && grid[scan][column] !== 'W'; scan++) {
          if (grid[scan][column] === 'E') columnCounts[column]++;
        }
      }
      if (grid[row][column] === '0') {
        best = Math.max(best, rowCount + columnCounts[column]);
      }
    }
  }
  return best;
}
