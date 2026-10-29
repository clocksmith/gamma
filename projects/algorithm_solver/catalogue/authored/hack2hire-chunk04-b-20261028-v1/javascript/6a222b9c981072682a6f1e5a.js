"use strict";
// Hack2Hire 6a222b9c981072682a6f1e5a (Build Transition Graph) over an INFERRED spec; qualification unknown.

function solve(logs) {
  const byUser = new Map();
  for (const [ts, user, resource] of logs) {
    if (!byUser.has(user)) byUser.set(user, []);
    byUser.get(user).push([Number(ts), resource]);
  }
  const counts = new Map();
  const bump = (a, b) => {
    const key = a + "\u0000" + b;
    const entry = counts.get(key);
    if (entry) entry[2]++;
    else counts.set(key, [a, b, 1]);
  };
  for (const entries of byUser.values()) {
    entries.sort((x, y) => x[0] - y[0]);
    let prev = "START";
    for (const [, resource] of entries) { bump(prev, resource); prev = resource; }
    bump(prev, "END");
  }
  const rows = [...counts.values()];
  rows.sort((x, y) => (x[0] < y[0] ? -1 : x[0] > y[0] ? 1 : x[1] < y[1] ? -1 : x[1] > y[1] ? 1 : 0));
  return rows;
}

function buildTransitionGraph(logs) { return solve(logs); }

module.exports = solve;
module.exports.buildTransitionGraph = buildTransitionGraph;
