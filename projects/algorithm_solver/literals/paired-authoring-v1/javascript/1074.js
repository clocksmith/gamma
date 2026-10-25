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
  numSubmatrixSumTarget(matrix, target) {
    const rows = matrix.length;
    const columns = rows > 0 ? matrix[0].length : 0;
    const prefix = matrixPrefix(matrix);
    let answer = 0;
    for (let top = 0; top < rows; top += 1) {
      for (let bottom = top + 1; bottom <= rows; bottom += 1) {
        const frequencies = new Map([[0, 1]]);
        let total = 0;
        for (let column = 0; column < columns; column += 1) {
          total += rectangleSum(prefix, top, column, bottom, column + 1);
          answer += frequencies.get(total - target) || 0;
          frequencies.set(total, (frequencies.get(total) || 0) + 1);
        }
      }
    }
    return answer;
  }
}
