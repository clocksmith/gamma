"use strict";
// Hack2Hire 6784b4640e1dbb6a09385784 (Dasher Payment Model, variant 3) over an INFERRED spec; qualification unknown.

const PEAKS = [[660, 840], [1020, 1200]]; // [11:00, 14:00) and [17:00, 20:00), weighted 2

function weightedBefore(t) {
  let total = t;
  for (const [start, end] of PEAKS) if (t > start) total += Math.min(t, end) - start;
  return total;
}

function solve(activities) {
  const cancelled = new Set();
  for (const row of activities) if (row[2] === "cancelled") cancelled.add(row[1]);
  let count = 0, paid = 0, previous = 0;
  for (const [time, order, event] of activities) {
    const t = Number(time.slice(0, 2)) * 60 + Number(time.slice(3));
    paid += count * (weightedBefore(t) - weightedBefore(previous));
    previous = t;
    if (cancelled.has(order)) continue;
    count += event === "accepted" ? 1 : -1;
  }
  return 30 * paid;
}

function calculatePay(activities) { return solve(activities); }

module.exports = solve;
module.exports.calculatePay = calculatePay;
