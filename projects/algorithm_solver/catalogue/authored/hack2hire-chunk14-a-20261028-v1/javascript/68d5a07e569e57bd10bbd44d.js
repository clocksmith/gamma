"use strict";
// Hack2Hire 68d5a07e569e57bd10bbd44d (Text Box Formatter, variant 2 of 3) over an INFERRED spec; qualification unknown.

function wrap(sentence, width) {
  const lines = [];
  let current = [], size = 0;
  for (const word of sentence.split(" ")) {
    if (current.length && size + 1 + word.length <= width) {
      current.push(word);
      size += 1 + word.length;
    } else {
      if (current.length) lines.push(current.join(" "));
      current = [word];
      size = word.length;
    }
  }
  lines.push(current.join(" "));
  return lines;
}

function solve(sentences, maxWidth) {
  const blocks = sentences.map((s) => wrap(s, maxWidth));
  let width = 0;
  for (const block of blocks) for (const line of block) if (line.length > width) width = line.length;
  const border = "+" + "-".repeat(width) + "+";
  const out = [];
  for (const block of blocks) {
    out.push(border);
    for (const line of block) out.push("|" + line.padEnd(width, " ") + "|");
    out.push(border);
  }
  return out;
}

function formatWrappedBoxes(sentences, maxWidth) { return solve(sentences, maxWidth); }

module.exports = solve;
module.exports.formatWrappedBoxes = formatWrappedBoxes;
