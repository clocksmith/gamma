"use strict";
// Hack2Hire 691523d03f8671d8f7a56571 (Design Persistent Key-Value Store, variant 1 of 2) over an INFERRED spec; qualification unknown.

function u32(n) { return [Math.floor(n / 16777216) % 256, (n >> 16) & 255, (n >> 8) & 255, n & 255]; }

function pushText(out, text) { for (let i = 0; i < text.length; i++) out.push(text.charCodeAt(i)); }

function parse(body) {
  // returns the entries of a level-1 body as a Map, or null when anything is malformed
  const size = body.length;
  const word = (i) => (i + 4 <= size ? ((body[i] * 256 + body[i + 1]) * 256 + body[i + 2]) * 256 + body[i + 3] : -1);
  const count = word(0);
  if (count < 0) return null;
  let i = 4, last = null;
  const out = new Map();
  for (let e = 0; e < count; e++) {
    let n = word(i);
    if (n < 1 || n > 10 || i + 4 + n > size) return null;
    const key = String.fromCharCode(...body.slice(i + 4, i + 4 + n));
    i += 4 + n;
    if (!/^[a-z0-9]+$/.test(key) || (last !== null && key <= last)) return null;
    n = word(i);
    if (n < 1 || n > 20 || i + 4 + n > size) return null;
    const value = String.fromCharCode(...body.slice(i + 4, i + 4 + n));
    i += 4 + n;
    if (!/^[ -~]+$/.test(value)) return null;
    out.set(key, value);
    last = key;
  }
  return i === size ? out : null;
}

class PersistentKVStore {
  constructor() { this.data = new Map(); }
  set(key, value) { this.data.set(key, value); }
  get(key) { const v = this.data.get(key); return v === undefined ? "" : v; }
  delete(key) { return this.data.delete(key); }

  save() {
    const body = u32(this.data.size);
    const keys = [...this.data.keys()].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
    for (const key of keys) {
      const value = this.data.get(key);
      body.push(...u32(key.length)); pushText(body, key);
      body.push(...u32(value.length)); pushText(body, value);
    }
    return body;
  }

  load(blob) { this.data = parse(blob); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "PersistentKVStore" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new PersistentKVStore(...argumentLists[0]);
  const allowed = new Set(["set", "get", "delete", "save", "load"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.PersistentKVStore = PersistentKVStore;
