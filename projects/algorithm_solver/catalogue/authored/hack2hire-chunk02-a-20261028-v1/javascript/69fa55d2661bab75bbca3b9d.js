"use strict";
// Hack2Hire 69fa55d2661bab75bbca3b9d (Maximize Hole in Prison Gate); INFERRED spec; qualification unknown.
function longestGap(removed) {
  const bars = removed.slice().sort((a, b) => a - b);
  let best = 0, run = 0;
  for (let i = 0; i < bars.length; i++) { run = i > 0 && bars[i] === bars[i - 1] + 1 ? run + 1 : 1; if (run > best) best = run; }
  return best + 1;
}
function solve(n, m, h, v) { return longestGap(h) * longestGap(v); }
function maximizeHole(n, m, h, v) { return solve(n, m, h, v); }
module.exports = solve;
module.exports.maximizeHole = maximizeHole;
