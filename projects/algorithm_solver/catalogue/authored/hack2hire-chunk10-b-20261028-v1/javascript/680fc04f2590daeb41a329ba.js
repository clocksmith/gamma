"use strict";
// Hack2Hire 680fc04f2590daeb41a329ba (Find Common Free Days, variant 3 of 3) over an INFERRED spec; qualification unknown.

function solve(blocks, totalDays, k) {
  const per = new Map();
  for (const [person, start, end] of blocks) {
    if (!per.has(person)) per.set(person, []);
    per.get(person).push([start, end]);
  }
  const events = [];
  for (const spans of per.values()) {
    spans.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    let [cs, ce] = spans[0];
    for (let i = 1; i < spans.length; i++) {
      const [s, e] = spans[i];
      if (s <= ce + 1) ce = Math.max(ce, e);
      else { events.push([cs, 1], [ce + 1, -1]); cs = s; ce = e; }
    }
    events.push([cs, 1], [ce + 1, -1]);
  }
  events.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const people = per.size, out = [];
  let busy = 0, i = 0, day = 1;
  while (day <= totalDays) {
    while (i < events.length && events[i][0] <= day) { busy += events[i][1]; i++; }
    const nxt = i < events.length ? events[i][0] : totalDays + 1;
    const end = Math.min(nxt - 1, totalDays);
    if (people - busy >= k) {
      if (out.length && out[out.length - 1][1] === day - 1) out[out.length - 1][1] = end;
      else out.push([day, end]);
    }
    day = end + 1;
  }
  return out;
}

function freeIntervalsForAtLeast(blocks, totalDays, k) { return solve(blocks, totalDays, k); }

module.exports = solve;
module.exports.freeIntervalsForAtLeast = freeIntervalsForAtLeast;
