"use strict";
// Hack2Hire 67799006dcf91f8e3c1c310d (Wildcard Matching) over an INFERRED spec; qualification unknown.

function solve(s, p) {
  if (!p.includes("*")) return s === p;
  const pieces = p.split("*");
  const first = pieces[0];
  const last = pieces[pieces.length - 1];
  if (first.length + last.length > s.length || !s.startsWith(first) || !s.endsWith(last)) return false;
  let position = first.length;
  const end = s.length - last.length;
  for (let i = 1; i < pieces.length - 1; i++) {
    const piece = pieces[i];
    if (!piece) continue;
    const found = s.indexOf(piece, position);
    if (found < 0 || found + piece.length > end) return false;
    position = found + piece.length;
  }
  return true;
}

function isMatch(s, p) { return solve(s, p); }

module.exports = solve;
module.exports.isMatch = isMatch;
