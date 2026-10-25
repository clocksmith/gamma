function matrixPrefix(matrix) {
  const rows = matrix.length;
  const columns = rows > 0 ? matrix[0].length : 0;
  const prefix = Array.from({length: rows + 1}, () => Array(columns + 1).fill(0));
  for (let row = 0; row < rows; row += 1) {
    let rowTotal = 0;
    for (let column = 0; column < columns; column += 1) {
      rowTotal += matrix[row][column];
      prefix[row + 1][column + 1] = prefix[row][column + 1] + rowTotal;
    }
  }
  return prefix;
}


function rectangleSum(prefix, top, left, bottom, right) {
  return prefix[bottom][right] - prefix[top][right] - prefix[bottom][left] + prefix[top][left];
}


class Solution {
  largest1BorderedSquare(grid) {
    const rows = grid.length;
    const columns = rows > 0 ? grid[0].length : 0;
    const prefix = matrixPrefix(grid);
    for (let side = Math.min(rows, columns); side > 0; side -= 1) {
      const required = side === 1 ? 1 : 4 * side - 4;
      for (let top = 0; top <= rows - side; top += 1) {
        for (let left = 0; left <= columns - side; left += 1) {
          const bottom = top + side;
          const right = left + side;
          let border = rectangleSum(prefix, top, left, bottom, right);
          if (side > 2) {
            border -= rectangleSum(prefix, top + 1, left + 1, bottom - 1, right - 1);
          }
          if (border === required) {
            return side * side;
          }
        }
      }
    }
    return 0;
  }
}
