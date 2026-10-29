"use strict";
// Hack2Hire 697690985ed12b33b05f0f2c (Shipping Route Cost Paths, variant 2 of 3) over an INFERRED spec; qualification unknown.

function solve(routes, source, target) {
  const outRoutes = new Map();
  for (const route of routes) {
    const [a, b, method, cost] = route.split(":");
    if (!outRoutes.has(a)) outRoutes.set(a, []);
    outRoutes.get(a).push([b, method, Number(cost)]);
  }
  const paths = [];
  for (const [middle, method, cost] of outRoutes.get(source) || []) {
    if (middle === target) { paths.push([source + ":" + method + ":" + target, cost]); continue; }
    for (const [end, method2, cost2] of outRoutes.get(middle) || []) {
      if (end === target) paths.push([source + ":" + method + ":" + middle + ":" + method2 + ":" + target, cost + cost2]);
    }
  }
  paths.sort((x, y) => x[1] - y[1] || (x[0] < y[0] ? -1 : x[0] > y[0] ? 1 : 0));
  return paths;
}

function pathsWithOneTransfer(routes, source, target) { return solve(routes, source, target); }

module.exports = solve;
module.exports.pathsWithOneTransfer = pathsWithOneTransfer;
