"use strict";
// Hack2Hire 687e65b7eab243475a7dfbf7 (Find Frequent Events in 24 Hours) over an INFERRED spec; qualification unknown.

function solve(logs, k) {
  const groups = new Map();
  for (const [user, stamp, event] of logs) {
    const key = user + "|" + event;
    let group = groups.get(key);
    if (group === undefined) { group = { event, times: [] }; groups.set(key, group); }
    group.times.push(stamp);
  }
  const found = new Set();
  for (const { event, times } of groups.values()) {
    if (found.has(event) || times.length < k) continue;
    times.sort((a, b) => a - b);
    for (let i = 0; i + k - 1 < times.length; i++) {
      if (times[i + k - 1] - times[i] < 86400) { found.add(event); break; }
    }
  }
  return Array.from(found).sort();
}

function findFrequentEvents(logs, k) { return solve(logs, k); }

module.exports = solve;
module.exports.findFrequentEvents = findFrequentEvents;
