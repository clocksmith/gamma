"use strict";
// Hack2Hire 6a8615b8701a76fc6843aed0 (Maximum Balanced Task Assignment) over an INFERRED spec; qualification unknown.

function solve(m, task) {
  const counts = new Map();
  for (const t of task) counts.set(t, (counts.get(t) || 0) + 1);
  let usable = 0;
  for (const c of counts.values()) usable += c < m ? c : m;
  return m * Math.floor(usable / m);
}

function maxBalancedTasks(m, task) { return solve(m, task); }

module.exports = solve;
module.exports.maxBalancedTasks = maxBalancedTasks;
