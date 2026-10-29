"use strict";
// Hack2Hire 67a56d81b571d6ff0a4bd238 (Bring Servers Down) over an INFERRED spec; qualification unknown.

function solve(request, health, k) {
  const hits = health.map((h) => (h - (h % k)) / k + (h % k ? 1 : 0));
  const order = Array.from({ length: request.length }, (_, i) => i);
  order.sort((i, j) => hits[i] * request[j] - hits[j] * request[i]);
  let total = 0;
  let elapsed = 0;
  for (const i of order) {
    elapsed += hits[i];
    total += request[i] * elapsed;
  }
  return total;
}

function getMinRequests(request, health, k) { return solve(request, health, k); }

module.exports = solve;
module.exports.getMinRequests = getMinRequests;
