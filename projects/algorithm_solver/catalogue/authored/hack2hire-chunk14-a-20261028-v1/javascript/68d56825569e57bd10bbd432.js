"use strict";
// Hack2Hire 68d56825569e57bd10bbd432 (Text Box Formatter, variant 1 of 3) over an INFERRED spec; qualification unknown.

function solve(sentences) {
  let width = 0;
  for (const s of sentences) if (s.length > width) width = s.length;
  const border = "+" + "-".repeat(width) + "+";
  const out = [];
  for (const sentence of sentences) out.push(border, "|" + sentence.padEnd(width, " ") + "|", border);
  return out;
}

function formatBoxes(sentences) { return solve(sentences); }

module.exports = solve;
module.exports.formatBoxes = formatBoxes;
