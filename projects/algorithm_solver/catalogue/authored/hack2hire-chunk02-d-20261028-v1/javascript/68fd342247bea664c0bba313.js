"use strict";
// Hack2Hire 68fd342247bea664c0bba313 (Find Earliest Available Meeting Slot) over an INFERRED spec; qualification unknown.

function minute(text) { return Number(text.slice(0, 2)) * 60 + Number(text.slice(3)); }

function format(m) { return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0"); }

function solve(events, k) {
  const busy = events.map((event) => { const parts = event.split(" "); return [minute(parts[2]), minute(parts[3])]; });
  busy.sort((p, q) => p[0] - q[0] || p[1] - q[1]);
  let freeFrom = 0; // first minute not covered by any busy interval seen so far
  for (const [start, end] of busy) {
    if (start - freeFrom >= k) return format(freeFrom);
    freeFrom = Math.max(freeFrom, end + 1);
  }
  return 1440 - freeFrom >= k ? format(freeFrom) : "-1";
}

function earliestMeetingSlot(events, k) { return solve(events, k); }

module.exports = solve;
module.exports.earliestMeetingSlot = earliestMeetingSlot;
