"use strict";
// Hack2Hire 6976850c5ed12b33b05f0f0f (Shipping Route Cost Paths, variant 1 of 3) over an INFERRED spec; qualification unknown.

function solve(routes, source, target) {
  const found = [];
  for (const route of routes) {
    const [a, b, method, cost] = route.split(":");
    if (a === source && b === target) found.push([method, Number(cost)]);
  }
  found.sort((x, y) => x[1] - y[1] || (x[0] < y[0] ? -1 : x[0] > y[0] ? 1 : 0));
  return found;
}

function directRoutes(routes, source, target) { return solve(routes, source, target); }

module.exports = solve;
module.exports.directRoutes = directRoutes;
