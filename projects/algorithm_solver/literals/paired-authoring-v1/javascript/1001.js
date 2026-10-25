function changeCount(counts, key, delta) {
  const updated = (counts.get(key) || 0) + delta;
  if (updated === 0) {
    counts.delete(key);
  } else {
    counts.set(key, updated);
  }
}


class Solution {
  gridIllumination(n, lamps, queries) {
    const active = new Set();
    const rows = new Map();
    const columns = new Map();
    const descending = new Map();
    const ascending = new Map();
    for (const [row, column] of lamps) {
      const key = `${row},${column}`;
      if (active.has(key)) {
        continue;
      }
      active.add(key);
      changeCount(rows, row, 1);
      changeCount(columns, column, 1);
      changeCount(descending, row - column, 1);
      changeCount(ascending, row + column, 1);
    }
    const output = [];
    for (const [row, column] of queries) {
      let illuminated = (rows.get(row) || 0) > 0 || (columns.get(column) || 0) > 0;
      illuminated = illuminated || (descending.get(row - column) || 0) > 0;
      illuminated = illuminated || (ascending.get(row + column) || 0) > 0;
      output.push(illuminated ? 1 : 0);
      for (let nextRow = row - 1; nextRow < row + 2; nextRow += 1) {
        for (let nextColumn = column - 1; nextColumn < column + 2; nextColumn += 1) {
          if (nextRow >= 0 && nextRow < n && nextColumn >= 0 && nextColumn < n) {
            const key = `${nextRow},${nextColumn}`;
            if (active.has(key)) {
              active.delete(key);
              changeCount(rows, nextRow, -1);
              changeCount(columns, nextColumn, -1);
              changeCount(descending, nextRow - nextColumn, -1);
              changeCount(ascending, nextRow + nextColumn, -1);
            }
          }
        }
      }
    }
    return output;
  }
}
