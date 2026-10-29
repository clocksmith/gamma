"use strict";
// Hack2Hire 69ff8062574d87bc49006e92 (Restore String with Target Digit Sum) over an INFERRED spec; qualification unknown.

function solve(pattern, targetSum, maxVal) {
  let slots = 0, rest = targetSum;
  for (const ch of pattern) { if (ch === "?") slots++; else rest -= ch.charCodeAt(0) - 48; }
  if (rest < 0 || rest > slots * maxVal) return "";
  const out = [];
  for (const ch of pattern) {
    if (ch !== "?") { out.push(ch); continue; }
    slots--;
    const digit = Math.max(0, rest - slots * maxVal);
    out.push(String(digit));
    rest -= digit;
  }
  return out.join("");
}

function restoreString(pattern, targetSum, maxVal) { return solve(pattern, targetSum, maxVal); }

module.exports = solve;
module.exports.restoreString = restoreString;
