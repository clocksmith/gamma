"use strict";
// Hack2Hire 67fda0b6d2adf72ba62b0ed9 (Gift Delivery Scheduler) over an INFERRED spec; qualification unknown.

function solve(intervals, n) {
  // byStart[s][e]: recipients available from hour s until hour e (e <= 17)
  const byStart = [];
  for (let s = 0; s < 18; s++) byStart.push(new Array(18).fill(0));
  for (const [start, end] of intervals) byStart[start][end]++;
  const waiting = new Array(18).fill(0); // waiting recipients by end hour: a bucket priority queue
  let served = 0;
  for (let hour = 9; hour < 17; hour++) {
    for (let end = hour + 1; end < 18; end++) waiting[end] += byStart[hour][end];
    waiting[hour] = 0; // availability ended
    let capacity = n;
    for (let end = hour + 1; end < 18 && capacity > 0; end++) {
      const take = Math.min(capacity, waiting[end]);
      waiting[end] -= take;
      capacity -= take;
      served += take;
    }
  }
  return served;
}

function maxDeliveries(intervals, n) { return solve(intervals, n); }

module.exports = solve;
module.exports.maxDeliveries = maxDeliveries;
