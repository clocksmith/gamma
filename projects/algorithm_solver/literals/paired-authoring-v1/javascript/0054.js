class Solution {
  spiralOrder(matrix) {
    if (matrix.length === 0 || matrix[0].length === 0) {
      return [];
    }

    const result = [];
    let top = 0;
    let bottom = matrix.length - 1;
    let left = 0;
    let right = matrix[0].length - 1;
    while (top <= bottom && left <= right) {
      for (let column = left; column <= right; column += 1) {
        result.push(matrix[top][column]);
      }
      top += 1;
      for (let row = top; row <= bottom; row += 1) {
        result.push(matrix[row][right]);
      }
      right -= 1;
      if (top <= bottom) {
        for (let column = right; column >= left; column -= 1) {
          result.push(matrix[bottom][column]);
        }
        bottom -= 1;
      }
      if (left <= right) {
        for (let row = bottom; row >= top; row -= 1) {
          result.push(matrix[row][left]);
        }
        left += 1;
      }
    }
    return result;
  }
}
