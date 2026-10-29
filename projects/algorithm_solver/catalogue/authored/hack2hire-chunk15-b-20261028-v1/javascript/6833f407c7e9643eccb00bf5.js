"use strict";
// Hack2Hire 6833f407c7e9643eccb00bf5 (Find Restaurant Intervals) over an INFERRED spec; qualification unknown.

function solve(open, close, capacity, reservations, partySize) {
  const events = [];
  for (const [start, end, seats] of reservations) {
    events.push([start, seats]);
    events.push([end, -seats]);
  }
  events.sort((x, y) => x[0] - y[0] || x[1] - y[1]);
  const result = [];
  let used = 0, current = open, begin = null, i = 0;
  for (;;) {
    const free = capacity - used >= partySize;
    if (free && begin === null) begin = current;
    if (!free && begin !== null) {
      if (current > begin) result.push([begin, current]);
      begin = null;
    }
    if (i === events.length) break;
    const t = events[i][0];
    while (i < events.length && events[i][0] === t) {
      used += events[i][1];
      i++;
    }
    current = t;
  }
  if (begin !== null && close > begin) result.push([begin, close]);
  const merged = [];
  for (const [a, b] of result) {
    if (merged.length && merged[merged.length - 1][1] === a) merged[merged.length - 1][1] = b;
    else merged.push([a, b]);
  }
  return merged;
}

function availableIntervals(open, close, capacity, reservations, partySize) { return solve(open, close, capacity, reservations, partySize); }

module.exports = solve;
module.exports.availableIntervals = availableIntervals;
