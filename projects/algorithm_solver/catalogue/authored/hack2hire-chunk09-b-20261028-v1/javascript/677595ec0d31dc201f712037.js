"use strict";
// Hack2Hire 677595ec0d31dc201f712037 (Connect Points in 2D Matrix) over an INFERRED spec; qualification unknown.

class PointMatrix {
  constructor() {
    this.points = new Set();
    this.rowPoints = new Map();
    this.colPoints = new Map();
    this.rowNode = new Map();
    this.colNode = new Map();
    this.parent = [];
  }

  _node(map, key) {
    let id = map.get(key);
    if (id === undefined) { id = this.parent.length; this.parent.push(id); map.set(key, id); }
    return id;
  }

  _find(x) {
    const parent = this.parent;
    let root = x;
    while (parent[root] !== root) root = parent[root];
    while (parent[x] !== root) { const next = parent[x]; parent[x] = root; x = next; }
    return root;
  }

  addPoint(row, col) {
    const key = row + ',' + col;
    if (this.points.has(key)) return undefined;
    this.points.add(key);
    if (!this.rowPoints.has(row)) this.rowPoints.set(row, []);
    if (!this.colPoints.has(col)) this.colPoints.set(col, []);
    this.rowPoints.get(row).push(col);
    this.colPoints.get(col).push(row);
    const a = this._find(this._node(this.rowNode, row)), b = this._find(this._node(this.colNode, col));
    if (a !== b) this.parent[a] = b;
    return undefined;
  }

  isConnected(point1, point2) {
    if (!this.points.has(point1[0] + ',' + point1[1]) || !this.points.has(point2[0] + ',' + point2[1])) return false;
    return this._find(this.rowNode.get(point1[0])) === this._find(this.rowNode.get(point2[0]));
  }

  getMinSteps(start, end) {
    const [sr, sc] = start, [er, ec] = end;
    if (!this.points.has(sr + ',' + sc) || !this.points.has(er + ',' + ec)) return -1;
    if (sr === er && sc === ec) return 0;
    if (this._find(this.rowNode.get(sr)) !== this._find(this.rowNode.get(er))) return -1;
    const seenRows = new Set([sr]), seenCols = new Set([sc]);
    let frontierRows = [sr], frontierCols = [sc], steps = 0;
    while (frontierRows.length || frontierCols.length) {
      const nextRows = [], nextCols = [];
      for (const row of frontierRows) {
        for (const col of this.rowPoints.get(row)) {
          if (row === er && col === ec) return steps + 1;
          if (!seenCols.has(col)) { seenCols.add(col); nextCols.push(col); }
        }
      }
      for (const col of frontierCols) {
        for (const row of this.colPoints.get(col)) {
          if (row === er && col === ec) return steps + 1;
          if (!seenRows.has(row)) { seenRows.add(row); nextRows.push(row); }
        }
      }
      frontierRows = nextRows; frontierCols = nextCols; steps++;
    }
    return -1;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "PointMatrix" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new PointMatrix(...argumentLists[0]);
  const allowed = new Set(["addPoint", "isConnected", "getMinSteps"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.PointMatrix = PointMatrix;
