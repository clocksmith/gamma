function* cardinalNeighbors(row, column, rows, columns) {
  for (const [rowStep, columnStep] of [[-1, 0], [0, 1], [1, 0], [0, -1]]) {
    const nextRow = row + rowStep;
    const nextColumn = column + columnStep;
    if (nextRow >= 0 && nextRow < rows && nextColumn >= 0 && nextColumn < columns) {
      yield [nextRow, nextColumn];
    }
  }
}


class Solution {
  exist(board, word) {
    if (word.length === 0) {
      return true;
    }
    const rows = board.length;
    const columns = rows > 0 ? board[0].length : 0;
    if (rows === 0 || columns === 0 || word.length > rows * columns) {
      return false;
    }
    const visited = Array.from({length: rows}, () => Array(columns).fill(false));
    for (let startRow = 0; startRow < rows; startRow += 1) {
      for (let startColumn = 0; startColumn < columns; startColumn += 1) {
        const stack = [[startRow, startColumn, 0, false]];
        while (stack.length > 0) {
          const [row, column, offset, expanded] = stack.pop();
          if (expanded) {
            visited[row][column] = false;
            continue;
          }
          if (visited[row][column] || board[row][column] !== word[offset]) {
            continue;
          }
          visited[row][column] = true;
          if (offset + 1 === word.length) {
            return true;
          }
          stack.push([row, column, offset, true]);
          for (const [nextRow, nextColumn] of cardinalNeighbors(row, column, rows, columns)) {
            if (!visited[nextRow][nextColumn]) {
              stack.push([nextRow, nextColumn, offset + 1, false]);
            }
          }
        }
      }
    }
    return false;
  }
}
