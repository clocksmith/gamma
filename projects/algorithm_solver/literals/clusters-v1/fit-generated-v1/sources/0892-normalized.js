function surfaceArea(matrixValues) {
  let resultCount = 0;
  for (let rowIndex = 0; rowIndex < matrixValues.length; rowIndex += 1) {
    const rowValues = matrixValues[rowIndex];
    for (let columnIndex = 0; columnIndex < rowValues.length; columnIndex += 1) {
      const value = rowValues[columnIndex];
      if (value !== 0) {
        resultCount += 2 + value * 4;
        if (rowIndex > 0) {
          resultCount -= Math.min(value, matrixValues[rowIndex - 1][columnIndex]) * 2;
        }
        if (columnIndex > 0) {
          resultCount -= Math.min(value, rowValues[columnIndex - 1]) * 2;
        }
      }
    }
  }
  return resultCount;
}
function solve(grid) {
  return surfaceArea(grid);
}
