function shortestDistance(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const size = rows * columns;
  const distance = new Float64Array(size);
  const reached = new Int32Array(size);
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  let buildings = 0;

  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) {
      if (grid[row][column] !== 1) continue;
      const queue = [row * columns + column];
      const visited = new Uint8Array(size);
      visited[queue[0]] = 1;
      let level = 0;
      let reachedThisBuilding = 0;

      for (let head = 0; head < queue.length;) {
        const currentLevelEnd = queue.length;
        while (head < currentLevelEnd) {
          const position = queue[head++];
          const currentRow = Math.floor(position / columns);
          const currentColumn = position % columns;
          for (const [deltaRow, deltaColumn] of directions) {
            const nextRow = currentRow + deltaRow;
            const nextColumn = currentColumn + deltaColumn;
            if (nextRow < 0 || nextRow >= rows || nextColumn < 0 || nextColumn >= columns) continue;
            const next = nextRow * columns + nextColumn;
            if (visited[next] || grid[nextRow][nextColumn] !== 0 || reached[next] !== buildings) continue;
            visited[next] = 1;
            reached[next]++;
            distance[next] += level + 1;
            reachedThisBuilding++;
            queue.push(next);
          }
        }
        level++;
      }
      if (reachedThisBuilding === 0) return -1;
      buildings++;
    }
  }

  let best = Infinity;
  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) {
      const index = row * columns + column;
      if (grid[row][column] === 0 && reached[index] === buildings) {
        best = Math.min(best, distance[index]);
      }
    }
  }
  return best === Infinity ? -1 : best;
}
