"use strict";
// Hack2Hire 68d9756679db2fbcd7d7db74 (Equal Frequency After One Deletion) over an INFERRED spec; qualification unknown.

function solve(s) {
  const counts = new Map();
  for (const ch of s) counts.set(ch, (counts.get(ch) || 0) + 1);
  const freq = new Map();
  for (const c of counts.values()) freq.set(c, (freq.get(c) || 0) + 1);
  if (freq.size === 1) return true;
  if (freq.size > 2) return false;
  const [[low, nlow], [high, nhigh]] = [...freq.entries()].sort((a, b) => a[0] - b[0]);
  return (low === 1 && nlow === 1) || (high === low + 1 && nhigh === 1);
}

function equalFrequency(s) { return solve(s); }

module.exports = solve;
module.exports.equalFrequency = equalFrequency;
