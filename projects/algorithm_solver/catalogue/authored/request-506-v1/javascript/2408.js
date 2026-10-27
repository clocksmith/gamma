// Original implementation. Contract: https://leetcode.com/problems/design-sql/
"use strict";

class SQL {
  constructor(names, columns) {
    this.tables = new Map(names.map((name, index) => [name, {
      columns: columns[index],
      next: 1,
      rows: new Map(),
    }]));
  }
  ins(name, row) {
    const table = this.tables.get(name);
    if (!table || row.length !== table.columns) return false;
    table.rows.set(table.next++, [...row]);
    return true;
  }
  rmv(name, id) {
    this.tables.get(name)?.rows.delete(id);
    return null;
  }
  sel(name, id, column) {
    const row = this.tables.get(name)?.rows.get(id);
    return row && column >= 1 && column <= row.length ? row[column - 1] : "<null>";
  }
  exp(name) {
    const table = this.tables.get(name);
    return table ? [...table.rows].map(([id, row]) => [id, ...row].join(",")) : [];
  }
}

function solve(operations, argumentsList) {
  let database;
  return operations.map((operation, index) => {
    if (operation === "SQL") {
      database = new SQL(...argumentsList[index]);
      return null;
    }
    return database[operation](...argumentsList[index]);
  });
}

module.exports = solve;
