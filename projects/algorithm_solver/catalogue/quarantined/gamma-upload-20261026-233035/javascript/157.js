'use strict';
// 157. Read N Characters Given Read4.
function solve(buf, n, read4Fn = globalThis.read4) {
  let written = 0;
  const temporary = Array(4);
  while (written < n) {
    const count = read4Fn(temporary);
    if (count === 0) break;
    for (let index = 0; index < Math.min(count, n - written); index += 1) buf[written++] = temporary[index];
  }
  return written;
}
class Solution { read(buf, n) { return solve(buf, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution };
