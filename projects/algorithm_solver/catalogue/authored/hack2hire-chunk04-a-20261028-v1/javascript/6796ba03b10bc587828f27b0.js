"use strict";
// Hack2Hire 6796ba03b10bc587828f27b0 (Valid Time Combinations) over an INFERRED spec; qualification unknown.

function solve(A, B, C, D) {
  const digits = [A, B, C, D], seen = new Set();
  for (let a = 0; a < 4; a++) for (let b = 0; b < 4; b++) for (let c = 0; c < 4; c++) for (let d = 0; d < 4; d++) {
    if (new Set([a, b, c, d]).size !== 4) continue;
    if (digits[a] * 10 + digits[b] < 24 && digits[c] * 10 + digits[d] < 60) seen.add('' + digits[a] + digits[b] + digits[c] + digits[d]);
  }
  return seen.size;
}

function countValidTimes(A, B, C, D) { return solve(A, B, C, D); }

module.exports = solve;
module.exports.countValidTimes = countValidTimes;
