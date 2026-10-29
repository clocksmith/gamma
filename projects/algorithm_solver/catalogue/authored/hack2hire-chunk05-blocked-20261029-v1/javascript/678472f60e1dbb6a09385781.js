"use strict";
// Hack2Hire 678472f60e1dbb6a09385781 (Dasher Payment Model, variant 1) over an INFERRED spec; qualification unknown.

const PEAKS = [];

function weightedBefore(t) {
  let total = t;
  for (const [start, end] of PEAKS) if (t > start) total += Math.min(t, end) - start;
  return total;
}

function solve(activities) {
  const cancelled = new Set();
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
