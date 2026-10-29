"use strict";
// Hack2Hire 68d5a07f569e57bd10bbd44e (Text Box Formatter, variant 3 of 3) over an INFERRED spec; qualification unknown.

function wrap(sentence, width) {
  const lines = [];
  let current = [], size = 0;
  for (const word of sentence.split(" ")) {
    if (current.length && size + 1 + word.length <= width) {
      current.push(word);
      size += 1 + word.length;
    } else {
      if (current.length) lines.push(current);
      current = [word];
      size = word.length;
    }
  }
  lines.push(current);
  return lines;
}

function justify(words, width) {
  const gaps = words.length - 1;
  let letters = 0;
  for (const w of words) letters += w.length;
  const spaces = width - letters;
  const base = Math.floor(spaces / gaps), extra = spaces % gaps;
  let line = words[0];
  for (let g = 0; g < gaps; g++) line += " ".repeat(base + (g < extra ? 1 : 0)) + words[g + 1];
  return line;
}

function solve(sentences, maxWidth) {
  const border = "+" + "-".repeat(maxWidth) + "+";
  const out = [];
  for (const sentence of sentences) {
    const lines = wrap(sentence, maxWidth);
    out.push(border);
    for (let i = 0; i < lines.length; i++) {
      const words = lines[i];
      const line = i < lines.length - 1 && words.length > 1 ? justify(words, maxWidth) : words.join(" ").padEnd(maxWidth, " ");
      out.push("|" + line + "|");
    }
    out.push(border);
  }
  return out;
}

function formatJustifiedBoxes(sentences, maxWidth) { return solve(sentences, maxWidth); }

module.exports = solve;
module.exports.formatJustifiedBoxes = formatJustifiedBoxes;
