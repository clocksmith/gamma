function* cardinalNeighbors(row, column, rows, columns) {
  for (const [rowStep, columnStep] of [[-1, 0], [0, 1], [1, 0], [0, -1]]) {
    const nextRow = row + rowStep;
    const nextColumn = column + columnStep;
    if (nextRow >= 0 && nextRow < rows && nextColumn >= 0 && nextColumn < columns) {
      yield [nextRow, nextColumn];
    }
  }
}


class Solution {
  colorBorder(grid, row, col, color) {
    const rows = grid.length;
    const columns = grid[0].length;
    const original = grid[row][col];
    const visited = Array.from({length: rows}, () => Array(columns).fill(false));
    visited[row][col] = true;
    const queue = [[row, col]];
    const border = [];
    let head = 0;
    while (head < queue.length) {
      const [currentRow, currentColumn] = queue[head];
      head += 1;
      let onBorder = currentRow === 0 || currentRow === rows - 1;
      onBorder = onBorder || currentColumn === 0 || currentColumn === columns - 1;
      for (const [nextRow, nextColumn] of cardinalNeighbors(currentRow, currentColumn, rows, columns)) {
        if (grid[nextRow][nextColumn] !== original) {
          onBorder = true;
        } else if (!visited[nextRow][nextColumn]) {
          visited[nextRow][nextColumn] = true;
          queue.push([nextRow, nextColumn]);
        }
      }
      if (onBorder) {
        border.push([currentRow, currentColumn]);
      }
    }
    for (const [borderRow, borderColumn] of border) {
      grid[borderRow][borderColumn] = color;
    }
    return grid;
  }
}
