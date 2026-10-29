"use strict";
// Hack2Hire 69d16c5617b72775cc49bf93 (Design Document Layer System, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
const ABSENT = Symbol("absent");
class Document {
  constructor() {
    this.layers = new Map();
    this.undoStack = []; // [layer, key, before, after]
  }
  put(layerId, key, value) {
    if (!this.layers.has(layerId)) this.layers.set(layerId, new Map());
    const layer = this.layers.get(layerId);
    if (value === ABSENT) layer.delete(key); else layer.set(key, value);
  }
  current(layerId, key) {
    const layer = this.layers.get(layerId);
    return layer !== undefined && layer.has(key) ? layer.get(key) : ABSENT;
  }
  change(layerId, key, after) {
    const before = this.current(layerId, key);
    this.put(layerId, key, after);
    this.undoStack.push([layerId, key, before, after]);
  }
  setProperty(layerId, key, value) { this.change(layerId, key, value); }
  getProperty(layerId, key) {
    const value = this.current(layerId, key);
    return value === ABSENT ? null : value;
  }
  undo() {
    if (!this.undoStack.length) return false;
    const entry = this.undoStack.pop();
    this.put(entry[0], entry[1], entry[2]);
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "Document" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new Document(...argumentLists[0]), allowed = new Set(["setProperty", "getProperty", "undo"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.Document = Document;
