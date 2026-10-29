"use strict";
// Hack2Hire 6827f7c3f13ac663af91d7a5 (Max Non-overlapping Tasks) over an INFERRED spec; qualification unknown.

function solve(tasks) {
  const order = tasks.map((t) => t).sort((a, b) => a[1] - b[1]);
  let count = 0, lastEnd = -1;
  for (const [start, end] of order) {
    if (start >= lastEnd) { count++; lastEnd = end; }
  }
  return count;
}

function maxNonOverlappingTasks(tasks) { return solve(tasks); }

module.exports = solve;
module.exports.maxNonOverlappingTasks = maxNonOverlappingTasks;
