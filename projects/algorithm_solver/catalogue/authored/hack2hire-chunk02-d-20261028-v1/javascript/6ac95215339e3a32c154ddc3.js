"use strict";
// Hack2Hire 6ac95215339e3a32c154ddc3 (Design a Rectangle Board, level 1) over an INFERRED spec; qualification unknown.

class RectangleBoard {
  constructor(width, height) {
    this.width = width;
    this.height = height;
    // flat per-id arrays (index = id); inactive ids stay in place and are skipped
    this.x1 = [0]; this.y1 = [0]; this.x2 = [0]; this.y2 = [0];
    this.key = [0];
    this.active = [false];
    this.nextKey = 0;
    this.history = [];
  }

  isActive(id) { return Number.isInteger(id) && id >= 1 && id < this.active.length && this.active[id]; }

  addRectangle(x1, y1, x2, y2) {
    const id = this.active.length;
    this.x1.push(x1); this.y1.push(y1); this.x2.push(x2); this.y2.push(y2);
    this.key.push(++this.nextKey);
    this.active.push(true);
    this.history.push(["add", id, 0]);
    return id;
  }

  getTopRectangle(x, y) {
    const {x1, y1, x2, y2, key, active} = this;
    let best = -1, bestKey = -1;
    for (let id = active.length - 1; id >= 1; id--) {
      if (active[id] && key[id] > bestKey && x1[id] <= x && x <= x2[id] && y1[id] <= y && y <= y2[id]) { best = id; bestKey = key[id]; }
    }
    return best;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "RectangleBoard" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new RectangleBoard(...argumentLists[0]);
  const allowed = new Set(["addRectangle", "getTopRectangle"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.RectangleBoard = RectangleBoard;
