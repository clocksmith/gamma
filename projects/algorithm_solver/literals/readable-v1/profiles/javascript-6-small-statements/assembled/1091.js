function shortestClearMatrixPath(gridValues) {
  if (gridValues[0][0]) {
    return (-1);
  }
  const gridSize = gridValues.length;
  gridValues[0][0] = 1;
  const queueValues = [[0, 0]];
  let queueIndex = 0;
  let pathLength = 1;
  while ((queueIndex < queueValues.length)) {
    const layerStop = queueValues.length;
    while ((queueIndex < layerStop)) {
      const rowIndex = queueValues[queueIndex][0];
      const columnIndex = queueValues[queueIndex][1];
      queueIndex += 1;
      if (((rowIndex === (gridSize - 1)) && (columnIndex === (gridSize - 1)))) {
        return pathLength;
      }
      for (let nextRow = (rowIndex - 1); (nextRow < (rowIndex + 2)); nextRow += 1) {
        for (let nextColumn = (columnIndex - 1); (nextColumn < (columnIndex + 2)); nextColumn += 1) {
          if ((((((nextRow >= 0) && (nextRow < gridSize)) && (nextColumn >= 0)) && (nextColumn < gridSize)) && (gridValues[nextRow][nextColumn] === 0))) {
            gridValues[nextRow][nextColumn] = 1;
            queueValues.push([nextRow, nextColumn]);
          }
        }
      }
    }
    pathLength += 1;
  }
  return (-1);
}
class Solution {
  shortestPathBinaryMatrix(grid) {
    return shortestClearMatrixPath(grid);
  }
}
