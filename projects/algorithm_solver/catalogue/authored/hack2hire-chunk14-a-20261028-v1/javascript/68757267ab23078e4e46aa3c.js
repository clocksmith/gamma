"use strict";
// Hack2Hire 68757267ab23078e4e46aa3c (Split Text into Lines) over an INFERRED spec; qualification unknown.

function solve(text, maxWidth) {
  let lines = 0;
  let current = 0;
  for (const word of text.split(" ")) {
    if (word.length === 0) continue;
    if (lines === 0 || current + 1 + word.length > maxWidth) {
      lines += 1;
      current = word.length;
    } else {
      current += 1 + word.length;
    }
  }
  return lines;
}

function minLines(text, maxWidth) { return solve(text, maxWidth); }

module.exports = solve;
module.exports.minLines = minLines;
