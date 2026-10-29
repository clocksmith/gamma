"use strict";
// Hack2Hire 696336dcf731aa3969ef52a7 (Maximum Concurrent Calls) over an INFERRED spec; qualification unknown.

const DAY = 86400000;

function solve(calls) {
  const events = new Map();
  for (const [customer, , start, end] of calls) {
    if (!events.has(customer)) events.set(customer, []);
    const bucket = events.get(customer);
    bucket.push([start, 1], [end, -1]);
  }
  const out = [];
  for (const customer of [...events.keys()].sort((a, b) => a - b)) {
    const list = events.get(customer).sort((a, b) => a[0] - b[0] || a[1] - b[1]); // ends before starts at equal times
    const peak = new Map();
    let active = 0, previous = 0;
    for (const [time, delta] of list) {
      if (active > 0 && time > previous) {
        for (let day = Math.floor(previous / DAY); day <= Math.floor((time - 1) / DAY); day++) {
          if ((peak.get(day) || 0) < active) peak.set(day, active);
        }
      }
      active += delta;
      previous = time;
    }
    for (const day of [...peak.keys()].sort((a, b) => a - b)) out.push([customer, day, peak.get(day)]);
  }
  return out;
}

function maxConcurrentCallsPerDay(calls) { return solve(calls); }

module.exports = solve;
module.exports.maxConcurrentCallsPerDay = maxConcurrentCallsPerDay;
