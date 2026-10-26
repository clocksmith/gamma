'use strict';

// 2187. Minimum Time to Complete Trips: binary search elapsed time and stop counting once the requested trips are reached.
// O(n * log(T + 1)) time and O(1) auxiliary space for T = min(time) * totalTrips; inputs are read-only.
function solve(time, totalTrips) {
  let fastest = Infinity;
  for (const duration of time) fastest = Math.min(fastest, duration);
  let low = 1;
  let high = fastest * totalTrips;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    let completed = 0;
    for (const duration of time) {
      completed += Math.floor(middle / duration);
      // Bounded counting avoids an unnecessarily large aggregate.
      if (completed >= totalTrips) break;
    }
    if (completed >= totalTrips) high = middle;
    else low = middle + 1;
  }
  return low;
}

const minimumTime = solve;
class Solution {
  minimumTime(time, totalTrips) { return solve(time, totalTrips); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTime };
