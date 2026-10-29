"use strict";
// Hack2Hire 67fc0d33216af53465a721dd (Minimum Swaps for Ball Grouping) over an INFERRED spec; qualification unknown.

function solve(balls) {
  const shifted = [];
  for (let i = 0; i < balls.length; i++) if (balls.charCodeAt(i) === 82) shifted.push(i - shifted.length);
  if (shifted.length <= 1) return 0;
  const median = shifted[shifted.length >> 1];
  let total = 0;
  for (const s of shifted) total += Math.abs(s - median);
  return total;
}

function minSwaps(balls) { return solve(balls); }

module.exports = solve;
module.exports.minSwaps = minSwaps;
