function transposeMatrix(matrixValues) {
  if (matrixValues.length === 0) {
    return [];
  }
  let columnCount = matrixValues[0].length;
  for (const rowValues of matrixValues) {
    columnCount = Math.min(columnCount, rowValues.length);
  }
  const resultValues = [];
  for (let columnIndex = 0; columnIndex < columnCount; columnIndex += 1) {
    const columnValues = [];
    for (const rowValues of matrixValues) {
      columnValues.push(rowValues[columnIndex]);
    }
    resultValues.push(columnValues);
  }
  return resultValues;
}
class Solution {
  transpose(matrix) {
    return transposeMatrix(matrix);
  }
}
