class Solution {
  generateMatrix(n) {
    const matrix = [];
    for (let row = 0; row < n; row += 1) {
      matrix.push(new Array(n).fill(0));
    }
    let top = 0;
    let bottom = n - 1;
    let left = 0;
    let right = n - 1;
    let value = 1;
    while (top <= bottom && left <= right) {
      for (let column = left; column <= right; column += 1) {
        matrix[top][column] = value;
        value += 1;
      }
      top += 1;
      for (let row = top; row <= bottom; row += 1) {
        matrix[row][right] = value;
        value += 1;
      }
      right -= 1;
      if (top <= bottom) {
        for (let column = right; column >= left; column -= 1) {
          matrix[bottom][column] = value;
          value += 1;
        }
        bottom -= 1;
      }
      if (left <= right) {
        for (let row = bottom; row >= top; row -= 1) {
          matrix[row][left] = value;
          value += 1;
        }
        left += 1;
      }
    }
    return matrix;
  }
}
