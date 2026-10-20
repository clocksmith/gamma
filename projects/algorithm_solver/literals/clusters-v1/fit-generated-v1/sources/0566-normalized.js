function filledMatrix(rowCount, columnCount, fillValue) {
  const resultMatrix = [];
  for (let rowIndex = 0; rowIndex < rowCount; rowIndex += 1) {
    resultMatrix.push(new Array(columnCount).fill(fillValue));
  }
  return resultMatrix;
}
function reshapeMatrix(matrix, targetRows, targetColumns) {
  const rowCount = matrix.length;
  const columnCount = matrix[0].length;
  const cellCount = rowCount * columnCount;
  if (cellCount !== targetRows * targetColumns) {
    return matrix;
  }
  const resultMatrix = filledMatrix(targetRows, targetColumns, 0);
  for (let cellIndex = 0; cellIndex < cellCount; cellIndex += 1) {
    resultMatrix[Math.floor(cellIndex / targetColumns)][cellIndex % targetColumns] = matrix[Math.floor(cellIndex / columnCount)][cellIndex % columnCount];
  }
  return resultMatrix;
}
function solve(mat, r, c) {
  return reshapeMatrix(mat, r, c);
}
