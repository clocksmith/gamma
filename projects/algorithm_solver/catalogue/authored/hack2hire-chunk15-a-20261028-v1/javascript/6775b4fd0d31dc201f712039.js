"use strict";
// Hack2Hire 6775b4fd0d31dc201f712039 (Count Days for Scheduled Tasks) over an INFERRED spec; qualification unknown.

function solve(intervals, goal) {
  const multiplicity = new Map();
  let smallest = Infinity;
  for (const interval of intervals) {
    multiplicity.set(interval, (multiplicity.get(interval) || 0) + 1);
    if (interval < smallest) smallest = interval;
  }
  const ivs = [], counts = [];
  for (const [interval, count] of multiplicity) { ivs.push(interval); counts.push(count); }

  function reaches(day) {
    const x = day - 1;
    let total = 0;
    for (let i = 0; i < ivs.length; i++) {
      total += ((x - x % ivs[i]) / ivs[i] + 1) * counts[i];
      if (total >= goal) return true;
    }
    return false;
  }

  let lo = 1, hi = 1 + (goal - 1) * smallest;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (reaches(mid)) hi = mid; else lo = mid + 1;
  }
  return lo;
}

function daysToGoal(intervals, goal) { return solve(intervals, goal); }

module.exports = solve;
module.exports.daysToGoal = daysToGoal;
