"use strict";
// Hack2Hire 68e1734e0fdcf62632c38cdc (Find Valid Sock Pairs, variant 2). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(ids, colors, feet) {
  const lefts = new Map(), rights = new Map();
  for (let i = 0; i < ids.length; i++) {
    const side = feet[i] === "left" ? lefts : rights;
    if (!side.has(colors[i])) side.set(colors[i], []);
    side.get(colors[i]).push(ids[i]);
  }
  const numeric = (a, b) => a - b, pairs = [];
  for (const [color, leftIds] of lefts) {
    const sortedLeft = leftIds.slice().sort(numeric), sortedRight = (rights.get(color) || []).slice().sort(numeric);
    const count = Math.min(sortedLeft.length, sortedRight.length);
    for (let i = 0; i < count; i++) pairs.push([sortedLeft[i], sortedRight[i]]);
  }
  return pairs.sort((a, b) => a[0] - b[0]);
}

function findSockPairs(ids, colors, feet) { return solve(ids, colors, feet); }
module.exports = solve;
module.exports.findSockPairs = findSockPairs;
