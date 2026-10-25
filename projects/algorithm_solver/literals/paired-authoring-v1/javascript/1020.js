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
  numEnclaves(grid) {
    const rows = grid.length;
    const columns = rows > 0 ? grid[0].length : 0;
    if (rows === 0 || columns === 0) {
      return 0;
    }
    const visited = Array.from({length: rows}, () => Array(columns).fill(false));
    const queue = [];
    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        if (row === 0 || row === rows - 1 || column === 0 || column === columns - 1) {
          if (grid[row][column] === 1) {
            visited[row][column] = true;
            queue.push([row, column]);
          }
        }
      }
    }
    let head = 0;
    while (head < queue.length) {
      const [row, column] = queue[head];
      head += 1;
      for (const [nextRow, nextColumn] of cardinalNeighbors(row, column, rows, columns)) {
        if (grid[nextRow][nextColumn] === 1 && !visited[nextRow][nextColumn]) {
          visited[nextRow][nextColumn] = true;
          queue.push([nextRow, nextColumn]);
        }
      }
    }
    let count = 0;
    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        if (grid[row][column] === 1 && !visited[row][column]) {
          count += 1;
        }
      }
    }
    return count;
  }
}
