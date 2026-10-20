function maximalSquare(matrix) {
  if (matrix.length === 0 || matrix[0].length === 0) {
    return 0;
  }

  const columns = matrix[0].length;
  const sizes = new Array(columns + 1).fill(0);
  let bestSide = 0;

  for (let row = 0; row < matrix.length; row += 1) {
    let previousDiagonal = 0;

    for (let column = 1; column <= columns; column += 1) {
      const previousAbove = sizes[column];

      if (
        matrix[row][column - 1] === '1' ||
        matrix[row][column - 1] === 1
      ) {
        sizes[column] = Math.min(
          sizes[column],
          sizes[column - 1],
          previousDiagonal
        ) + 1;
        bestSide = Math.max(bestSide, sizes[column]);
      } else {
        sizes[column] = 0;
      }

      previousDiagonal = previousAbove;
    }
  }

  return bestSide * bestSide;
}
