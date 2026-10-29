"use strict";

function solve(slots1, slots2, duration) {
  const a = slots1.filter((s) => s[1] - s[0] >= duration).sort((x, y) => x[0] - y[0]);
  const b = slots2.filter((s) => s[1] - s[0] >= duration).sort((x, y) => x[0] - y[0]);
  let i = 0, j = 0;
  while (i < a.length && j < b.length) {
    const lo = a[i][0] > b[j][0] ? a[i][0] : b[j][0];
    const hi = a[i][1] < b[j][1] ? a[i][1] : b[j][1];
    if (hi - lo >= duration) return [lo, lo + duration];
    if (a[i][1] < b[j][1]) i++;
    else j++;
  }
  return [];
}

function minAvailableDuration(slots1, slots2, duration) {
  return solve(slots1, slots2, duration);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minAvailableDuration = minAvailableDuration;
