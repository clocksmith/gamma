"use strict";
// Hack2Hire 67d44fdf488516fd8ad5a0ba (Design Recent File Tracker) over an INFERRED spec; qualification unknown.

const BLOCK = 512;

function invertDate(date) {
  // inverted date digits sort newest first
  let out = "";
  for (const c of date) out += c >= "0" && c <= "9" ? String.fromCharCode(105 - c.charCodeAt(0)) : c;
  return out;
}

class FileStorageSystem {
  constructor() { this.blocks = []; this.inserted = []; } // sorted blocks of keys "<inverted date><name>"

  storeFile(file, date) {
    const key = invertDate(date) + file, blocks = this.blocks;
    this.inserted.push(file);
    if (!blocks.length) { blocks.push([key]); return; }
    let i = 0;
    while (i < blocks.length - 1 && blocks[i][blocks[i].length - 1] < key) i += 1;
    const block = blocks[i];
    let lo = 0, hi = block.length;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (block[mid] < key) lo = mid + 1; else hi = mid; }
    block.splice(lo, 0, key);
    if (block.length > 2 * BLOCK) blocks.splice(i, 1, block.slice(0, BLOCK), block.slice(BLOCK));
  }

  getKthRecentFiles(k) {
    const out = [];
    for (const block of this.blocks) {
      for (let j = 0; j < block.length && out.length < k; j++) out.push(block[j].slice(10));
      if (out.length >= k) break;
    }
    return out;
  }

  returnAllFiles() { return this.inserted.slice(); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "FileStorageSystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new FileStorageSystem(...argumentLists[0]);
  const allowed = new Set(["storeFile", "getKthRecentFiles", "returnAllFiles"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.FileStorageSystem = FileStorageSystem;
