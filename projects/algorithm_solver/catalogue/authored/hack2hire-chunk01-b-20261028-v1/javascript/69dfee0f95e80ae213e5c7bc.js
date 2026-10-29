"use strict";
// Hack2Hire 69dfee0f95e80ae213e5c7bc (Find Text Before Stop Words, variant 2: streamed chunks). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(chunks, stopWords) {
  const prefixes = new Set();
  let longest = 0;
  for (const word of stopWords) {
    longest = Math.max(longest, word.length);
    for (let i = 1; i < word.length; i++) prefixes.add(word.slice(0, i));
  }
  const earliest = (text) => {
    let found = -1;
    for (const word of stopWords) {
      const position = text.indexOf(word);
      if (position >= 0 && (found < 0 || position < found)) found = position;
    }
    return found;
  };
  const out = [];
  let pending = "", stopped = false;
  for (const chunk of chunks) {
    if (stopped) {
      out.push("");
      continue;
    }
    pending += chunk;
    let hold = pending.length;
    for (let start = Math.max(0, pending.length - longest + 1); start < pending.length; start++) {
      if (prefixes.has(pending.slice(start))) {
        hold = start;
        break;
      }
    }
    const position = earliest(pending);
    if (position >= 0 && position <= hold) {
      out.push(pending.slice(0, position));
      pending = "";
      stopped = true;
    } else {
      out.push(pending.slice(0, hold));
      pending = pending.slice(hold);
    }
  }
  if (stopped) out.push("");
  else {
    const position = earliest(pending);
    out.push(position < 0 ? pending : pending.slice(0, position));
  }
  return out;
}

function streamBeforeStopWords(chunks, stopWords) { return solve(chunks, stopWords); }
module.exports = solve;
module.exports.streamBeforeStopWords = streamBeforeStopWords;
