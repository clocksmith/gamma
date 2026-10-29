"use strict";
// Hack2Hire 69d1730e17b72775cc49bfc6 (Design Document Layer System, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
const ABSENT = Symbol("absent");
class Document {
  constructor() {
    this.layers = new Map();
    this.undoStack = []; // [layer, key, before, after]
    this.redoStack = [];
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
    this.redoStack.length = 0;
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
    this.redoStack.push(entry);
    return true;
  }
  redo() {
    if (!this.redoStack.length) return false;
    const entry = this.redoStack.pop();
    this.put(entry[0], entry[1], entry[3]);
    this.undoStack.push(entry);
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "Document" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new Document(...argumentLists[0]), allowed = new Set(["setProperty", "getProperty", "undo", "redo"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.Document = Document;
