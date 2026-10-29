"use strict";
// Hack2Hire 6a18e226c81f779dc6a230e4 (Fit Saved Rectangles in a Box); INFERRED spec; qualification unknown.
function solve(operations) {
  let shortSide = 0, longSide = 0;
  const out = [];
  for (const [kind, a, b] of operations) {
    const low = Math.min(a, b), high = Math.max(a, b);
    if (kind === 0) { shortSide = Math.max(shortSide, low); longSide = Math.max(longSide, high); }
    else out.push(shortSide <= low && longSide <= high);
  }
  return out;
}
function fitSavedRectangles(operations) { return solve(operations); }
module.exports = solve;
module.exports.fitSavedRectangles = fitSavedRectangles;
