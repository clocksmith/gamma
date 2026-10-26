'use strict';

// 1883. Minimum Skips to Arrive at Meeting On Time.
// Use integer distance-units to avoid floating-point rounding; O(n^2) time, O(n) space. Inputs are preserved.

function solve(dist, speed, hoursBefore) {
  const n = dist.length, deadline = speed * hoursBefore;
  if (dist.reduce((sum, value) => sum + value, 0) > deadline) return -1;
  let times = Array(n + 1).fill(Infinity);
  times[0] = 0;
  for (let road = 0; road < n; road += 1) {
    const following = Array(n + 1).fill(Infinity);
    for (let skipped = 0; skipped <= road; skipped += 1) {
      const arrival = times[skipped] + dist[road];
      const waited = road === n - 1 ? arrival : Math.ceil(arrival / speed) * speed;
      following[skipped] = Math.min(following[skipped], waited);
      if (road !== n - 1) following[skipped + 1] = Math.min(following[skipped + 1], arrival);
    }
    times = following;
  }
  return times.findIndex(time => time <= deadline);
}

const minSkips = solve;
class Solution {
  minSkips(dist, speed, hoursBefore) { return solve(dist, speed, hoursBefore); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSkips };
