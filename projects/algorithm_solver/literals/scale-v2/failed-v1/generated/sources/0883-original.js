function projectionArea(matrixValues) {
  if (matrixValues.length === 0) {
    return 0;
  }
  let columnCount = matrixValues[0].length;
  let resultCount = 0;
  for (const rowValues of matrixValues) {
    columnCount = Math.min(columnCount, rowValues.length);
    let maximumValue = rowValues[0];
    for (const value of rowValues) {
      if (value > 0) {
        resultCount += 1;
      }
      maximumValue = Math.max(maximumValue, value);
    }
    resultCount += maximumValue;
  }
  for (let columnIndex = 0; columnIndex < columnCount; columnIndex += 1) {
    let maximumValue = matrixValues[0][columnIndex];
    for (const rowValues of matrixValues) {
      maximumValue = Math.max(maximumValue, rowValues[columnIndex]);
    }
    resultCount += maximumValue;
  }
  return resultCount;
}
class Solution {
  projectionArea(grid) {
    return projectionArea(grid);
  }
}
