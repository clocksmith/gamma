"use strict";
// Hack2Hire 699f7bb56e73e4abccc9b565 (Rank Vehicles by Contribution) over an INFERRED spec; qualification unknown.

function solve(events) {
  const sent = new Map();
  for (const [source, chunkList, target] of events) {
    if (source !== "server") {
      let chunks = 1;
      for (let i = 0; i < chunkList.length; i++) if (chunkList.charCodeAt(i) === 32) chunks++;
      sent.set(source, (sent.get(source) || 0) + chunks);
    }
    if (!sent.has(target)) sent.set(target, 0);
  }
  return [...sent.keys()].sort((a, b) => (sent.get(b) - sent.get(a)) || (a < b ? -1 : a > b ? 1 : 0));
}

function rankVehicles(events) { return solve(events); }

module.exports = solve;
module.exports.rankVehicles = rankVehicles;
