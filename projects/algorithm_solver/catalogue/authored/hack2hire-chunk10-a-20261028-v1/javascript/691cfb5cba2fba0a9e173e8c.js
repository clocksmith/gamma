"use strict";
// Hack2Hire 691cfb5cba2fba0a9e173e8c (Design In-Memory SQL) over an INFERRED spec; qualification unknown.

const INTEGER = /^(?:0|-?[1-9][0-9]{0,8})$/;

function test(op, a, b) {
  switch (op) {
    case "=": return a === b;
    case "!=": return a !== b;
    case "<": return a < b;
    case "<=": return a <= b;
    case ">": return a > b;
    default: return a >= b;
  }
}

class Table {
  constructor(columns) {
    this.columns = columns.slice();
    this.index = new Map(columns.map((name, i) => [name, i]));
    this.types = null; // booleans (true = integer) fixed by the first stored row
    this.rows = []; // [original strings, typed values]
  }
}

class SQLManager {
  constructor() { this.tables = new Map(); }

  createTable(tableName, columnNames) { this.tables.set(tableName, new Table(columnNames)); }

  insert(tableName, values) {
    const table = this.tables.get(tableName);
    if (table === undefined || values.length !== table.columns.length) return false;
    const kinds = values.map((v) => INTEGER.test(v));
    if (table.types !== null && kinds.some((k, i) => k !== table.types[i])) return false;
    table.types = kinds;
    table.rows.push([values.slice(), values.map((v, i) => (kinds[i] ? Number(v) : v))]);
    return true;
  }

  select(tableName, conditions, orderBy, ascending) {
    const table = this.tables.get(tableName);
    if (table === undefined || table.rows.length === 0 || (orderBy !== "" && !table.index.has(orderBy))) return [];
    const tests = [];
    for (const [column, op, literal] of conditions) {
      const i = table.index.get(column);
      if (i === undefined) return [];
      let lit = literal;
      if (table.types[i]) {
        if (!INTEGER.test(literal)) return []; // a non-integer literal matches no integer value
        lit = Number(literal);
      }
      tests.push([i, op, lit]);
    }
    const hits = table.rows.filter((row) => tests.every(([i, op, lit]) => test(op, row[1][i], lit)));
    if (orderBy !== "") {
      const j = table.index.get(orderBy), sign = ascending ? 1 : -1;
      hits.sort((a, b) => (a[1][j] < b[1][j] ? -sign : a[1][j] > b[1][j] ? sign : 0)); // stable in both directions
    }
    return hits.map((row) => row[0].slice());
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "SQLManager" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new SQLManager(...argumentLists[0]);
  const allowed = new Set(["createTable", "insert", "select"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.SQLManager = SQLManager;
