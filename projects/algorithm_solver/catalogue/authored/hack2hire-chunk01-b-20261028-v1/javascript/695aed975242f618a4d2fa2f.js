"use strict";
// Hack2Hire 695aed975242f618a4d2fa2f (Design a Buffered File Writer). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

class BufferedFile {
  constructor(capacity, file = null) {
    this.capacity = capacity;
    this.buffer = new Array(capacity).fill(0);
    this.size = 0;
    this.file = file;
  }
  _drain(out) {
    for (let i = 0; i < this.size; i++) {
      if (this.file !== null) this.file.write(this.buffer[i]);
      out.push(this.buffer[i]);
    }
    this.size = 0;
  }
  write(data) {
    const out = [];
    let i = 0;
    while (i < data.length) {
      const take = Math.min(this.capacity - this.size, data.length - i);
      for (let j = 0; j < take; j++) this.buffer[this.size + j] = data[i + j];
      this.size += take;
      i += take;
      if (this.size === this.capacity) this._drain(out);
    }
    return out;
  }
  flush() {
    const out = [];
    if (this.size) this._drain(out);
    return out;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "BufferedFile" || argumentLists[0].length !== 1) throw new Error("exact constructor required");
  const instance = new BufferedFile(argumentLists[0][0]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (operationNames[i] === "write") result.push(instance.write(argumentLists[i][0]));
    else if (operationNames[i] === "flush" && argumentLists[i].length === 0) result.push(instance.flush());
    else throw new Error("unknown method");
  }
  return result;
}

module.exports = solve;
module.exports.BufferedFile = BufferedFile;
