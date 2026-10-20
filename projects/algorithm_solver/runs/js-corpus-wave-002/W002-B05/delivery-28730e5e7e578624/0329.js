function longestIncreasingPath(matrix) {
  if (matrix.length === 0 || matrix[0].length === 0) return 0;
  const rows = matrix.length;
  const columns = matrix[0].length;
  const size = rows * columns;
  const outdegree = new Uint8Array(size);
  const queue = new Int32Array(size);
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  let tail = 0;

  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) {
      const position = row * columns + column;
      for (const [deltaRow, deltaColumn] of directions) {
        const nextRow = row + deltaRow;
        const nextColumn = column + deltaColumn;
        if (nextRow >= 0 && nextRow < rows && nextColumn >= 0 && nextColumn < columns &&
          matrix[nextRow][nextColumn] > matrix[row][column]) outdegree[position]++;
      }
      if (outdegree[position] === 0) queue[tail++] = position;
    }
  }

  let head = 0;
  let length = 0;
  while (head < tail) {
    const boundary = tail;
    length++;
    while (head < boundary) {
      const position = queue[head++];
      const row = Math.floor(position / columns);
      const column = position % columns;
      for (const [deltaRow, deltaColumn] of directions) {
        const nextRow = row + deltaRow;
        const nextColumn = column + deltaColumn;
        if (nextRow < 0 || nextRow >= rows || nextColumn < 0 || nextColumn >= columns ||
          matrix[nextRow][nextColumn] >= matrix[row][column]) continue;
        const next = nextRow * columns + nextColumn;
        outdegree[next]--;
        if (outdegree[next] === 0) queue[tail++] = next;
      }
    }
  }
  return length;
}
