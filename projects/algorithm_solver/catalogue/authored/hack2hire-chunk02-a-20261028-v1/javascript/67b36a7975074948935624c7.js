"use strict";
// Hack2Hire 67b36a7975074948935624c7 (MultiStream Reader); INFERRED spec, streams injected as strings; qualification unknown.
const CHUNK = 4;
class Stream {  // read-only stream; only read(n) is used by the reader
  constructor(data) { this._data = data; this._pos = 0; }
  read(n) { const piece = this._data.slice(this._pos, this._pos + n); this._pos += piece.length; return piece; }
}
class MultiStreamReader {
  constructor(streams) { this.streams = streams.map(s => new Stream(s)); this.current = 0; this.pending = ''; }
  read(n) {
    const parts = [];
    let need = n;
    if (this.pending) { const take = this.pending.slice(0, need); parts.push(take); this.pending = this.pending.slice(take.length); need -= take.length; }
    while (need > 0 && this.current < this.streams.length) {
      const chunk = this.streams[this.current].read(Math.max(CHUNK, need));
      if (chunk === '') { this.current++; continue; }
      parts.push(chunk.slice(0, need)); this.pending = chunk.slice(need); need -= Math.min(need, chunk.length);
    }
    return parts.join('');
  }
}
function solve(operations, args) {
  const receiver = new MultiStreamReader(...args[0]), out = [null];
  for (let i = 1; i < operations.length; i++) { const v = receiver[operations[i]](...args[i]); out.push(v === undefined ? null : v); }
  return out;
}
module.exports = solve;
module.exports.MultiStreamReader = MultiStreamReader;
