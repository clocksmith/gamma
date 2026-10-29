"use strict";
// Hack2Hire 69fa8ff5661bab75bbca3e10 (Count Dropped Requests) over an INFERRED spec; qualification unknown.

function solve(requestTime) {
  let dropped = 0;
  for (let i = 0; i < requestTime.length; i++) {
    const t = requestTime[i];
    if ((i >= 3 && requestTime[i - 3] === t) || (i >= 20 && t - requestTime[i - 20] < 10) || (i >= 60 && t - requestTime[i - 60] < 60)) dropped++;
  }
  return dropped;
}

function droppedRequests(requestTime) { return solve(requestTime); }

module.exports = solve;
module.exports.droppedRequests = droppedRequests;
