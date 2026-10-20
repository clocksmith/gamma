function hasConstantDiagonals(matrixValues) {
  const rowCount = matrixValues.length;
  const columnCount = matrixValues[0].length;
  for (let rowIndex = 1; rowIndex < rowCount; rowIndex += 1) {
    for (let columnIndex = 1; columnIndex < columnCount; columnIndex += 1) {
      if (matrixValues[rowIndex][columnIndex] !== matrixValues[rowIndex - 1][columnIndex - 1]) {
        return false;
      }
    }
  }
  return true;
}
function solve(matrix) {
  return hasConstantDiagonals(matrix);
}
