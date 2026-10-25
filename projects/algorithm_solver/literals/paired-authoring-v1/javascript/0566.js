class Solution {
  matrixReshape(mat, r, c) {
    if (mat.length * mat[0].length !== r * c) {
      return mat;
    }

    const result = [];
    for (let row = 0; row < r; row += 1) {
      result.push(new Array(c).fill(0));
    }
    let output_row = 0;
    let output_column = 0;
    for (const row of mat) {
      for (const value of row) {
        result[output_row][output_column] = value;
        output_column += 1;
        if (output_column === c) {
          output_column = 0;
          output_row += 1;
        }
      }
    }
    return result;
  }
}
