"use strict";
// Hack2Hire 69f3a12f42791c82ab992d99 (User Flight Location Tracker) over an INFERRED spec; qualification unknown.

function solve(flights, userId, time) {
  const legs = flights.filter((f) => f[4] === userId).sort((a, b) => (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
  if (!legs.length) return "";
  let lo = 0, hi = legs.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (legs[mid][1] <= time) lo = mid + 1; else hi = mid; }
  const i = lo - 1;
  if (i < 0) return legs[0][0];
  const [origin, departure, destination, arrival] = legs[i];
  if (time === departure) return origin;
  if (time < arrival) return "";
  return destination;
}

function findUserLocation(flights, userId, time) { return solve(flights, userId, time); }

module.exports = solve;
module.exports.findUserLocation = findUserLocation;
