"use strict";

function solve(intervals, k) {
  const arr = intervals.map((x) => [x[0], x[1]]).sort((a, b) => (a[0] !== b[0] ? a[0] - b[0] : a[1] - b[1]));
  const merged = [];
  for (let i = 0; i < arr.length; i++) {
    const [s, e] = arr[i];
    if (merged.length === 0 || s > merged[merged.length - 1][1]) {
      merged.push([s, e]);
    } else if (e > merged[merged.length - 1][1]) {
      merged[merged.length - 1][1] = e;
    }
  }
  const m = merged.length;
  let maxBridge = 0;
  let r = 0;
  for (let l = 0; l < m; l++) {
    while (r < m && merged[r][0] <= merged[l][1] + k) r++;
    if (r - 1 - l > maxBridge) maxBridge = r - 1 - l;
  }
  return m - maxBridge;
}

function minConnectedGroups(intervals, k) {
  return solve(intervals, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minConnectedGroups = minConnectedGroups;
