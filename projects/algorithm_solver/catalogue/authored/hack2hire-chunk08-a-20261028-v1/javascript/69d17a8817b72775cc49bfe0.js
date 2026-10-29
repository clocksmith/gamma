"use strict";
// Hack2Hire 69d17a8817b72775cc49bfe0 (Select Table and Set Color) over an INFERRED spec; qualification unknown.

class Table {
  constructor(numRows, numColumns) {
    this.columns = numColumns; this.stamp = 0; this.table = [0, ""];
    this.rows = new Map(); this.cells = new Map(); this.selection = null;
  }

  selectTable() { this.selection = ["table"]; }

  selectRow(row) { this.selection = ["row", row]; }

  selectCell(row, col) { this.selection = ["cell", row * this.columns + col]; }

  setColor(color) {
    if (this.selection === null) return;
    this.stamp += 1;
    const kind = this.selection[0];
    if (kind === "table") this.table = [this.stamp, color];
    else if (kind === "row") this.rows.set(this.selection[1], [this.stamp, color]);
    else this.cells.set(this.selection[1], [this.stamp, color]);
  }

  getColor(row, col) {
    let best = this.table;
    let painted = this.rows.get(row);
    if (painted !== undefined && painted[0] > best[0]) best = painted;
    painted = this.cells.get(row * this.columns + col);
    if (painted !== undefined && painted[0] > best[0]) best = painted;
    return best[1];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "Table" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new Table(...argumentLists[0]);
  const allowed = new Set(["selectTable", "selectRow", "selectCell", "setColor", "getColor"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.Table = Table;
