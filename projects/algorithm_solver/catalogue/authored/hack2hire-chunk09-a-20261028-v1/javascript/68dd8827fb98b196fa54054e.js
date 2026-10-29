"use strict";
// Hack2Hire 68dd8827fb98b196fa54054e (Build Smallest Number, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(nums) {
  const parts = nums.map(String);
  parts.sort((a, b) => { const ab = a + b, ba = b + a; return ab < ba ? -1 : ab > ba ? 1 : 0; });
  if (parts[0] !== "0") return parts.join("");
  if (parts.every((p) => p === "0")) return "0";
  let best = null;
  const tried = new Set();
  for (let i = 0; i < parts.length; i++) {
    const p = parts[i];
    if (p === "0" || tried.has(p)) continue;
    tried.add(p);
    const candidate = p + parts.slice(0, i).join("") + parts.slice(i + 1).join("");
    if (best === null || candidate < best) best = candidate;
  }
  return best;
}

function smallestConcatenation(nums) { return solve(nums); }

module.exports = solve;
module.exports.smallestConcatenation = smallestConcatenation;
