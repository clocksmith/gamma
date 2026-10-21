function toggleLowBit(value) {
  if (value % 2 === 0) {
    return value + 1;
  }
  return value - 1;
}
function flipInvertImage(matrixValues) {
  const rowCount = matrixValues.length;
  for (const rowValues of matrixValues) {
    let leftIndex = 0;
    let rightIndex = rowCount - 1;
    while (leftIndex < rightIndex) {
      if (rowValues[leftIndex] === rowValues[rightIndex]) {
        rowValues[leftIndex] = toggleLowBit(rowValues[leftIndex]);
        rowValues[rightIndex] = toggleLowBit(rowValues[rightIndex]);
      }
      leftIndex += 1;
      rightIndex -= 1;
    }
    if (leftIndex === rightIndex) {
      rowValues[leftIndex] = toggleLowBit(rowValues[leftIndex]);
    }
  }
  return matrixValues;
}
class Solution {
  flipAndInvertImage(image) {
    return flipInvertImage(image);
  }
}
