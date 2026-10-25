class Solution {
  transpose(matrix) {
    const rows = matrix.length;
    const columns = rows > 0 ? matrix[0].length : 0;
    const output = Array.from({length: columns}, () => Array(rows).fill(0));
    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        output[column][row] = matrix[row][column];
      }
    }
    return output;
  }
}
