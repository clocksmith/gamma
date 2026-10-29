"use strict";
// Hack2Hire 6787150fe20f8f324213c295 (CPU Usage Analysis) over an INFERRED spec; qualification unknown.

function solve(logs) {
  const stack = [], total = new Map();
  let previous = 0;
  for (const [name, action, ts] of logs) {
    const t = Number(ts);
    if (stack.length) { const top = stack[stack.length - 1]; total.set(top, total.get(top) + t - previous); }
    previous = t;
    if (action === "enter") { stack.push(name); if (!total.has(name)) total.set(name, 0); }
    else stack.pop();
  }
  const names = [...total.keys()].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  return names.map((n) => [n, total.get(n)]);
}

function exclusiveTimes(logs) { return solve(logs); }

module.exports = solve;
module.exports.exclusiveTimes = exclusiveTimes;
