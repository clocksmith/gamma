"use strict";
// Hack2Hire 68f599dba269f53ea0eff890 (One-Hot Encoding of An Array) over an INFERRED spec; qualification unknown.

function solve(arr) {
  const values = Array.from(new Set(arr)).sort((a, b) => a - b);
  const index = new Map();
  values.forEach((v, i) => index.set(v, i));
  const out = [];
  for (const x of arr) {
    const row = new Array(values.length).fill(0);
    row[index.get(x)] = 1;
    out.push(row);
  }
  return out;
}

function oneHotEncode(arr) { return solve(arr); }

module.exports = solve;
module.exports.oneHotEncode = oneHotEncode;
