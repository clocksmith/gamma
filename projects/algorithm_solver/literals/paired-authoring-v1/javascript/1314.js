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
  matrixBlockSum(mat, k) {
    const rows = mat.length;
    const columns = rows > 0 ? mat[0].length : 0;
    const prefix = matrixPrefix(mat);
    const output = Array.from({length: rows}, () => Array(columns).fill(0));
    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        const top = Math.max(0, row - k);
        const left = Math.max(0, column - k);
        const bottom = Math.min(rows, row + k + 1);
        const right = Math.min(columns, column + k + 1);
        output[row][column] = rectangleSum(prefix, top, left, bottom, right);
      }
    }
    return output;
  }
}
