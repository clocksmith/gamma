"use strict";
// Hack2Hire 69cd7029ff3ebde766cee760 (Stream to Matrix Row Transformer) over an INFERRED spec; qualification unknown.

function solve(codes, records) {
  const columns = codes.slice().sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  const index = new Map(columns.map((code, i) => [code, i]));
  const groups = new Map();
  for (const [timestamp, code, value] of records) {
    if (!index.has(code)) continue;
    let g = groups.get(timestamp);
    if (!g) { g = []; groups.set(timestamp, g); }
    g.push(index.get(code), value);
  }
  const current = new Array(columns.length).fill(null);
  const rows = [];
  const times = Array.from(groups.keys()).sort((a, b) => a - b);
  for (const timestamp of times) {
    const g = groups.get(timestamp);
    for (let i = 0; i < g.length; i += 2) current[g[i]] = g[i + 1];
    rows.push([timestamp, ...current]);
  }
  return rows;
}

function buildRows(codes, records) { return solve(codes, records); }

module.exports = solve;
module.exports.buildRows = buildRows;
