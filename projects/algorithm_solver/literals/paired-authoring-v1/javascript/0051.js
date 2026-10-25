class Solution {
  solveNQueens(n) {
    const columns = new Array(n).fill(false);
    const descending = new Array(2 * n + 1).fill(false);
    const ascending = new Array(2 * n + 1).fill(false);
    const placement = [];
    const boards = [];

    function collect(row) {
      if (row === n) {
        const board = [];
        for (const column of placement) {
          board.push(".".repeat(column) + "Q" + ".".repeat(n - column - 1));
        }
        boards.push(board);
        return;
      }
      for (let column = 0; column < n; column += 1) {
        const down = row - column + n;
        const up = row + column;
        if (columns[column] || descending[down] || ascending[up]) {
          continue;
        }
        columns[column] = true;
        descending[down] = true;
        ascending[up] = true;
        placement.push(column);
        collect(row + 1);
        placement.pop();
        columns[column] = false;
        descending[down] = false;
        ascending[up] = false;
      }
    }

    collect(0);
    return boards;
  }
}
