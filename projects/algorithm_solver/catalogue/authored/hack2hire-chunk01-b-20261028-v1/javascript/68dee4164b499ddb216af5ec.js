"use strict";
// Hack2Hire 68dee4164b499ddb216af5ec (Find Valid Sock Pairs, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(ids, colors, feet) {
  const lefts = new Map(), rights = new Map();
  for (let i = 0; i < colors.length; i++) {
    const side = feet[i] === "left" ? lefts : rights;
    side.set(colors[i], (side.get(colors[i]) || 0) + 1);
  }
  let pairs = 0;
  for (const [color, count] of lefts) pairs += Math.min(count, rights.get(color) || 0);
  return pairs;
}

function countSockPairs(ids, colors, feet) { return solve(ids, colors, feet); }
module.exports = solve;
module.exports.countSockPairs = countSockPairs;
