function minTotalDistance(grid) {
  const rows = [], columns = [];
  for (let row = 0; row < grid.length; row++) for (let col = 0; col < grid[row].length; col++) {
    if (grid[row][col] === 1) { rows.push(row); columns.push(col); }
  }
  if (!rows.length) return 0;
  columns.sort((a, b) => a - b);
  const rowMedian = rows[Math.floor(rows.length / 2)];
  const colMedian = columns[Math.floor(columns.length / 2)];
  return rows.reduce((sum, value) => sum + Math.abs(value - rowMedian), 0) +
    columns.reduce((sum, value) => sum + Math.abs(value - colMedian), 0);
}
