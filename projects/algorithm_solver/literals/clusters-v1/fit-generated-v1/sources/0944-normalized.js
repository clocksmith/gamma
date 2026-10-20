function unsortedColumnCount(wordRows) {
  const characterRows = [];
  for (const wordText of wordRows) {
    characterRows.push(Array.from(wordText));
  }
  const columnCount = characterRows[0].length;
  let resultCount = 0;
  for (let columnIndex = 0; columnIndex < columnCount; columnIndex += 1) {
    for (let rowIndex = 1; rowIndex < characterRows.length; rowIndex += 1) {
      if (characterRows[rowIndex][columnIndex].codePointAt(0) < characterRows[rowIndex - 1][columnIndex].codePointAt(0)) {
        resultCount += 1;
        break;
      }
    }
  }
  return resultCount;
}
function solve(strs) {
  return unsortedColumnCount(strs);
}
