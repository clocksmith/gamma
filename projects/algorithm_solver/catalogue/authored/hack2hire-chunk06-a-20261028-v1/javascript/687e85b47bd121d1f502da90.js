"use strict";
// Hack2Hire 687e85b47bd121d1f502da90 (Find Smallest Hub) over an INFERRED spec; qualification unknown.

function solve(capacities, intervals, requiredCapacity, taskInterval) {
  let colon = taskInterval.indexOf(':');
  const start = Number(taskInterval.slice(0, colon)), end = Number(taskInterval.slice(colon + 1));
  let best = -1;
  for (let i = 0; i < capacities.length; i++) {
    const capacity = capacities[i];
    if (capacity < requiredCapacity || (best >= 0 && capacity >= capacities[best])) continue;
    let free = true;
    for (const booking of intervals[i]) {
      colon = booking.indexOf(':');
      if (Number(booking.slice(0, colon)) <= end && start <= Number(booking.slice(colon + 1))) { free = false; break; }
    }
    if (free) best = i;
  }
  return best;
}

function findSmallestHub(capacities, intervals, requiredCapacity, taskInterval) { return solve(capacities, intervals, requiredCapacity, taskInterval); }

module.exports = solve;
module.exports.findSmallestHub = findSmallestHub;
