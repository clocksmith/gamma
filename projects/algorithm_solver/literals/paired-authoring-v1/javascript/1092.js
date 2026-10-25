class Solution {
  shortestCommonSupersequence(str1, str2) {
    const rows = str1.length;
    const columns = str2.length;
    const lengths = Array.from({length: rows + 1}, () => Array(columns + 1).fill(0));
    for (let row = 0; row <= rows; row += 1) {
      lengths[row][columns] = rows - row;
    }
    for (let column = 0; column <= columns; column += 1) {
      lengths[rows][column] = columns - column;
    }
    for (let row = rows - 1; row >= 0; row -= 1) {
      for (let column = columns - 1; column >= 0; column -= 1) {
        if (str1[row] === str2[column]) {
          lengths[row][column] = 1 + lengths[row + 1][column + 1];
        } else {
          lengths[row][column] = 1 + Math.min(lengths[row + 1][column], lengths[row][column + 1]);
        }
      }
    }
    const result = [];
    let row = 0;
    let column = 0;
    while (row < rows && column < columns) {
      if (str1[row] === str2[column]) {
        result.push(str1[row]);
        row += 1;
        column += 1;
      } else if (lengths[row + 1][column] <= lengths[row][column + 1]) {
        result.push(str1[row]);
        row += 1;
      } else {
        result.push(str2[column]);
        column += 1;
      }
    }
    while (row < rows) {
      result.push(str1[row]);
      row += 1;
    }
    while (column < columns) {
      result.push(str2[column]);
      column += 1;
    }
    return result.join("");
  }
}
