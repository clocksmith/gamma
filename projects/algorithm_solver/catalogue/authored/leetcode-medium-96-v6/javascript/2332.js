'use strict';

// 2332. The Latest Time to Catch a Bus: simulate boarding on sorted copies and move the final feasible arrival off occupied times.
// O(b log b + p log p) time and O(b + p) auxiliary space; inputs are read-only.
function solve(buses, passengers, capacity) {
  const departures = buses.slice().sort((left, right) => left - right);
  const arrivals = passengers.slice().sort((left, right) => left - right);
  let index = 0;
  let boarded = 0;
  for (const departure of departures) {
    boarded = 0;
    while (index < arrivals.length && arrivals[index] <= departure && boarded < capacity) {
      index += 1;
      boarded += 1;
    }
  }
  let candidate = boarded < capacity ? departures[departures.length - 1] : arrivals[index - 1];
  const occupied = new Set(arrivals);
  while (occupied.has(candidate)) candidate -= 1;
  return candidate;
}

const latestTimeCatchTheBus = solve;
class Solution {
  latestTimeCatchTheBus(buses, passengers, capacity) { return solve(buses, passengers, capacity); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, latestTimeCatchTheBus };
