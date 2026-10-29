"use strict";
// Hack2Hire 67888093402dc47b67a14948 (Number of Idle Drives) over an INFERRED spec; qualification unknown.

function solve(x, y) {
  const column = new Map(), row = new Map();
  for (let i = 0; i < x.length; i++) {
    const a = x[i], b = y[i];
    const c = column.get(a);
    if (c === undefined) column.set(a, [b, b]);
    else { if (b < c[0]) c[0] = b; if (b > c[1]) c[1] = b; }
    const r = row.get(b);
    if (r === undefined) row.set(b, [a, a]);
    else { if (a < r[0]) r[0] = a; if (a > r[1]) r[1] = a; }
  }
  let count = 0;
  for (let i = 0; i < x.length; i++) {
    const c = column.get(x[i]), r = row.get(y[i]);
    if (c[0] < y[i] && y[i] < c[1] && r[0] < x[i] && x[i] < r[1]) count++;
  }
  return count;
}

function countIdleDrives(x, y) { return solve(x, y); }

module.exports = solve;
module.exports.countIdleDrives = countIdleDrives;
