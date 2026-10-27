'use strict';
// 158. Read N Characters Given Read4 II - Call Multiple Times.
class Solution {
  constructor() { this.buffer = Array(4); this.start = 0; this.end = 0; }
  read(buf, n) {
    let written = 0;
    while (written < n) {
      if (this.start === this.end) {
        this.end = globalThis.read4(this.buffer);
        this.start = 0;
        if (this.end === 0) break;
      }
      while (written < n && this.start < this.end) buf[written++] = this.buffer[this.start++];
    }
    return written;
  }
}
function solve(read4Fn, requests) {
  const old = globalThis.read4;
  globalThis.read4 = read4Fn;
  try {
    const reader = new Solution();
    return requests.map(n => {
      const buf = Array(n);
      const count = reader.read(buf, n);
      return buf.slice(0, count).join('');
    });
  } finally { globalThis.read4 = old; }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution };
