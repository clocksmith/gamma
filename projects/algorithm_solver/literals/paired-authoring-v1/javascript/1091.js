class Solution {
  shortestPathBinaryMatrix(grid) {
    const size = grid.length;
    if (grid[0][0] !== 0) {
      return -1;
    }
    grid[0][0] = 1;
    const queue = [[0, 0, 1]];
    let head = 0;
    while (head < queue.length) {
      const [row, column, distance] = queue[head];
      head += 1;
      if (row === size - 1 && column === size - 1) {
        return distance;
      }
      for (const rowStep of [-1, 0, 1]) {
        for (const columnStep of [-1, 0, 1]) {
          if (rowStep === 0 && columnStep === 0) {
            continue;
          }
          const nextRow = row + rowStep;
          const nextColumn = column + columnStep;
          if (nextRow >= 0 && nextRow < size && nextColumn >= 0 && nextColumn < size) {
            if (grid[nextRow][nextColumn] === 0) {
              grid[nextRow][nextColumn] = 1;
              queue.push([nextRow, nextColumn, distance + 1]);
            }
          }
        }
      }
    }
    return -1;
  }
}
