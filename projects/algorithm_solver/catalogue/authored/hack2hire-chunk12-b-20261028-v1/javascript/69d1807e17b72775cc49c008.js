"use strict";
// Hack2Hire 69d1807e17b72775cc49c008 (Nested String with Brackets Parsing, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(s) {
  let depth = 0;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (ch === "(") depth++;
    else if (ch === ")") { depth--; if (depth < 0) return false; }
  }
  return depth === 0;
}

function isWellFormed(s) { return solve(s); }

module.exports = solve;
module.exports.isWellFormed = isWellFormed;
