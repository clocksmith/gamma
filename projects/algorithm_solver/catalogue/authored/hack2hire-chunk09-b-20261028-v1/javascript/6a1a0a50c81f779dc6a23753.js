"use strict";
// Hack2Hire 6a1a0a50c81f779dc6a23753 (Credit Card Fraud Detection, variant 1 of 3) over an INFERRED spec; qualification unknown.

function solve(requests) {
  const parsed = requests.map((s) => { const f = s.split(','); return [Number(f[0]), f[1]]; });
  parsed.sort((x, y) => x[0] - y[0]);  // Array.prototype.sort is stable, so ties keep input order
  return parsed.map((row) => [row[1], 'APPROVE']);
}

function processRequests(requests) { return solve(requests); }

module.exports = solve;
module.exports.processRequests = processRequests;
