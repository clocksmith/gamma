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
  maxDistance(grid) {
    const size = grid.length;
    const queue = [];
    for (let row = 0; row < size; row += 1) {
      for (let column = 0; column < size; column += 1) {
        if (grid[row][column] === 1) {
          queue.push([row, column, 0]);
        }
      }
    }
    if (queue.length === 0 || queue.length === size * size) {
      return -1;
    }
    let head = 0;
    let furthest = 0;
    while (head < queue.length) {
      const [row, column, distance] = queue[head];
      head += 1;
      for (const [nextRow, nextColumn] of cardinalNeighbors(row, column, size, size)) {
        if (grid[nextRow][nextColumn] === 0) {
          grid[nextRow][nextColumn] = 1;
          const nextDistance = distance + 1;
          furthest = Math.max(furthest, nextDistance);
          queue.push([nextRow, nextColumn, nextDistance]);
        }
      }
    }
    return furthest;
  }
}
