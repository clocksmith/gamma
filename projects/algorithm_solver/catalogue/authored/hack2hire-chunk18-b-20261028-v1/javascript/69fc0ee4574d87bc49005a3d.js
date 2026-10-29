"use strict";
// Hack2Hire 69fc0ee4574d87bc49005a3d (Data Labeling Task Scheduler, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(totalTask, totalModel, totalHuman, k) {
  if (k > totalHuman || k > totalModel) return [];
  // least loaded, smallest index first is round robin over the global assignment number q
  const out = [];
  let q = 0;
  for (let t = 1; t <= totalTask; t++) {
    const task = "t" + t;
    for (let j = 0; j < k; j++) {
      out.push([task, "m" + ((q % totalModel) + 1), "h" + ((q % totalHuman) + 1)]);
      q += 1;
    }
  }
  return out;
}

function scheduleTasks(totalTask, totalModel, totalHuman, k) { return solve(totalTask, totalModel, totalHuman, k); }

module.exports = solve;
module.exports.scheduleTasks = scheduleTasks;
