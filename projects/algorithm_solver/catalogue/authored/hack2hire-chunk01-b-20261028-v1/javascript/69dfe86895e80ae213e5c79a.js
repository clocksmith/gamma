"use strict";
// Hack2Hire 69dfe86895e80ae213e5c79a (Find Text Before Stop Words, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(text, stopWords) {
  let cut = text.length;
  for (const word of stopWords) {
    const position = text.indexOf(word);
    if (position >= 0 && position < cut) cut = position;
  }
  return text.slice(0, cut);
}

function textBeforeStopWords(text, stopWords) { return solve(text, stopWords); }
module.exports = solve;
module.exports.textBeforeStopWords = textBeforeStopWords;
