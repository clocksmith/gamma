function newGrid(rows, columns) {
  const grid = [];
  for (let row = 0; row < rows; row += 1) {
    grid.push(new Array(columns).fill(0));
  }
  return grid;
}

class Solution {
  findPaths(m, n, maxMove, startRow, startColumn) {
    const modulus = 1000000007;
    let ways = newGrid(m, n);
    ways[startRow][startColumn] = 1;
    let escaped = 0;
    const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    for (let move = 0; move < maxMove; move += 1) {
      const next_ways = newGrid(m, n);
      for (let row = 0; row < m; row += 1) {
        for (let column = 0; column < n; column += 1) {
          const count = ways[row][column];
          if (count === 0) {
            continue;
          }
          for (const [row_step, column_step] of directions) {
            const next_row = row + row_step;
            const next_column = column + column_step;
            const outside = next_row < 0 || next_row >= m
              || next_column < 0 || next_column >= n;
            if (outside) {
              escaped = (escaped + count) % modulus;
            } else {
              const previous = next_ways[next_row][next_column];
              next_ways[next_row][next_column] = (previous + count) % modulus;
            }
          }
        }
      }
      ways = next_ways;
    }
    return escaped;
  }
}
