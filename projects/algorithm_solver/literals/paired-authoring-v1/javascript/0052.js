class Solution {
  totalNQueens(n) {
    const columns = new Array(n).fill(false);
    const descending = new Array(2 * n + 1).fill(false);
    const ascending = new Array(2 * n + 1).fill(false);

    function count_from(row) {
      if (row === n) {
        return 1;
      }
      let total = 0;
      for (let column = 0; column < n; column += 1) {
        const down = row - column + n;
        const up = row + column;
        if (columns[column] || descending[down] || ascending[up]) {
          continue;
        }
        columns[column] = true;
        descending[down] = true;
        ascending[up] = true;
        total += count_from(row + 1);
        columns[column] = false;
        descending[down] = false;
        ascending[up] = false;
      }
      return total;
    }

    return count_from(0);
  }
}
