'use strict';

// 1870. Minimum Speed to Arrive on Time: binary search speed using exact hundredths for the final arrival comparison.
// O(n * log(10^7)) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(dist, hour) {
  const hundredths = Math.round(hour * 100);
  function feasible(speed) {
    let wholeHours = 0;
    for (let index = 0; index < dist.length - 1; index += 1) {
      wholeHours += Math.floor((dist[index] + speed - 1) / speed);
      if (wholeHours * 100 >= hundredths) return false;
    }
    const remaining = hundredths - wholeHours * 100;
    return BigInt(dist[dist.length - 1]) * 100n <= BigInt(remaining) * BigInt(speed);
  }
  let low = 1;
  let high = 10000000;
  if (!feasible(high)) return -1;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (feasible(middle)) high = middle;
    else low = middle + 1;
  }
  return low;
}

const minSpeedOnTime = solve;
class Solution {
  minSpeedOnTime(dist, hour) { return solve(dist, hour); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSpeedOnTime };
