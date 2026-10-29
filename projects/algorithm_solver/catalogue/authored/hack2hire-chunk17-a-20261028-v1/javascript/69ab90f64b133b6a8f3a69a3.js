"use strict";
// Hack2Hire 69ab90f64b133b6a8f3a69a3 (Thread Logs Processing, variant 2 of 2) over an INFERRED spec; qualification unknown.

function parse(entry) {
  const a = entry.indexOf(":");
  const b = entry.indexOf(":", a + 1);
  const c = entry.indexOf(":", b + 1);
  return [entry.slice(0, a), entry.slice(a + 1, b), Number(entry.slice(b + 1, c))];
}

function compare(x, y) { return x < y ? -1 : x > y ? 1 : 0; }

function solve(logs) {
  const stats = new Map(); // "processId:threadId" -> [processId, threadId, count, first, last]
  for (const entry of logs) {
    const [process, thread, t] = parse(entry);
    const key = process + ":" + thread;
    const row = stats.get(key);
    if (row === undefined) stats.set(key, [process, thread, 1, t, t]);
    else {
      row[2]++;
      if (t < row[3]) row[3] = t;
      if (t > row[4]) row[4] = t;
    }
  }
  const rows = Array.from(stats.values());
  rows.sort((x, y) => compare(x[0], y[0]) || compare(x[1], y[1]));
  return rows.map((r) => r.join(":"));
}

function summarizeThreads(logs) { return solve(logs); }

module.exports = solve;
module.exports.summarizeThreads = summarizeThreads;
