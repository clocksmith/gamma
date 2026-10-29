"use strict";
// Hack2Hire 69ab8d9d4b133b6a8f3a699f (Thread Logs Processing, variant 1 of 2) over an INFERRED spec; qualification unknown.

function parse(entry) {
  const a = entry.indexOf(":");
  const b = entry.indexOf(":", a + 1);
  const c = entry.indexOf(":", b + 1);
  return [entry.slice(0, a), entry.slice(a + 1, b), Number(entry.slice(b + 1, c))];
}

function compare(x, y) { return x < y ? -1 : x > y ? 1 : 0; }

function solve(logs) {
  const keys = logs.map((entry, index) => [...parse(entry), index]);
  keys.sort((x, y) => compare(x[0], y[0]) || compare(x[1], y[1]) || (x[2] - y[2]) || (x[3] - y[3]));
  return keys.map((key) => logs[key[3]]);
}

function sortLogs(logs) { return solve(logs); }

module.exports = solve;
module.exports.sortLogs = sortLogs;
