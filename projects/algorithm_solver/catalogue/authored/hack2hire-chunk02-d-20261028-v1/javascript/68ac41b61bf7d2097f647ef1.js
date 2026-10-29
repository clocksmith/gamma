"use strict";
// Hack2Hire 68ac41b61bf7d2097f647ef1 (Design Request Rate limiter) over an INFERRED spec; qualification unknown.

function solve(timestamps, windowSize, maxRequests) {
  const kept = [];
  let head = 0;
  const result = [];
  for (const t of timestamps) {
    const low = t - windowSize + 1;
    while (head < kept.length && kept[head] < low) head++;
    const allowed = kept.length - head < maxRequests;
    if (allowed) kept.push(t);
    result.push(allowed);
  }
  return result;
}

function rateLimit(timestamps, windowSize, maxRequests) { return solve(timestamps, windowSize, maxRequests); }

module.exports = solve;
module.exports.rateLimit = rateLimit;
