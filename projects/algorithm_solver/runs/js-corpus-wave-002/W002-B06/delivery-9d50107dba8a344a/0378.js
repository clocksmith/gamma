function kthSmallest(matrix, k) {
  const rows = matrix.length;
  const columns = matrix[0].length;
  let low = matrix[0][0];
  let high = matrix[rows - 1][columns - 1];

  function countAtMost(value) {
    let count = 0;
    let column = columns - 1;
    for (let row = 0; row < rows; row++) {
      while (column >= 0 && matrix[row][column] > value) column--;
      count += column + 1;
    }
    return count;
  }

  while (low < high) {
    const middle = low + Math.floor((high - low) / 2);
    if (countAtMost(middle) < k) low = middle + 1;
    else high = middle;
  }
  return low;
}
