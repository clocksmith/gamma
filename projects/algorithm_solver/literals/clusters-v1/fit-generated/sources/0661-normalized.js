function smoothImage(grid) {
  const rowCount = grid.length;
  const columnCount = grid[0].length;
  const resultRows = [];
  for (let rowIndex = 0; rowIndex < rowCount; rowIndex += 1) {
    const resultRow = [];
    for (let columnIndex = 0; columnIndex < columnCount; columnIndex += 1) {
      let neighborSum = 0;
      let neighborCount = 0;
      for (let neighborRowIndex = rowIndex - 1; neighborRowIndex < rowIndex + 2; neighborRowIndex += 1) {
        for (let neighborColumnIndex = columnIndex - 1; neighborColumnIndex < columnIndex + 2; neighborColumnIndex += 1) {
          if (neighborRowIndex >= 0 && neighborRowIndex < rowCount && neighborColumnIndex >= 0 && neighborColumnIndex < columnCount) {
            neighborSum += grid[neighborRowIndex][neighborColumnIndex];
            neighborCount += 1;
          }
        }
      }
      resultRow.push(Math.floor(neighborSum / neighborCount));
    }
    resultRows.push(resultRow);
  }
  return resultRows;
}
function solve(img) {
  return smoothImage(img);
}
