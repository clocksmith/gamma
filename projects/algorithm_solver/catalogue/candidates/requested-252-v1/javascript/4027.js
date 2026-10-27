/**
 * 4027. Elevator Requests III
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/elevator-requests-iii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4027.Elevator%20Requests%20III/README_EN.md
 * Complexity: O(q^2 log U) time, O(q) space; U bounds finishing time.
 * Binary search finish time T. Reverse time: releases become deadlines T-arrival, final floor is free, and the route ends at start by time T. Earliest reversed arrival dominates later arrivals. Visited request floors form an interval, yielding exact interval DP. Repeated floors retain only latest release. Inputs preserved; new derivation is unexecuted.
 */

function solve(n, start, requests) {
  const arrivals = new Map();
  for (const [time, floor] of requests) arrivals.set(floor, Math.max(arrivals.get(floor) || 0, time));
  const points = Array.from(arrivals.keys()).sort((a, b) => a - b), releases = points.map(x => arrivals.get(x)), count = points.length;
  let low = 0;
  for (const value of releases) low = Math.max(low, value);
  let high = low + points[count - 1] - points[0] + Math.min(Math.abs(start - points[0]), Math.abs(start - points[count - 1]));
  function feasible(finish) {
    let left = new Float64Array(count), right = new Float64Array(count);
    for (let length = 2; length <= count; length++) {
      const nextLeft = new Float64Array(count - length + 1).fill(Infinity), nextRight = new Float64Array(count - length + 1).fill(Infinity);
      for (let lo = 0; lo + length <= count; lo++) {
        const hi = lo + length - 1;
        const a = Math.min(left[lo + 1] + points[lo + 1] - points[lo], right[lo + 1] + points[hi] - points[lo]);
        if (a <= finish - releases[lo]) nextLeft[lo] = a;
        const b = Math.min(left[lo] + points[hi] - points[lo], right[lo] + points[hi] - points[hi - 1]);
        if (b <= finish - releases[hi]) nextRight[lo] = b;
      }
      left = nextLeft; right = nextRight;
    }
    return Math.min(left[0] + Math.abs(points[0] - start), right[0] + Math.abs(points[count - 1] - start)) <= finish;
  }
  while (low < high) { const middle = Math.floor((low + high) / 2); if (feasible(middle)) high = middle; else low = middle + 1; }
  return low;
}

function elevatorRequests(n, start, requests) {
  return solve(n, start, requests);
}

class Solution {
  elevatorRequests(n, start, requests) {
    return solve(n, start, requests);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, elevatorRequests, Solution };
}
