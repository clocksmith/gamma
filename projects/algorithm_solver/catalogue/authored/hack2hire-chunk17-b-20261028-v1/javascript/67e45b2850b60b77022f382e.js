"use strict";
// Hack2Hire 67e45b2850b60b77022f382e (Word Pattern Match) over an INFERRED spec; qualification unknown.

function solve(pattern, words) {
  const result = [];
  for (const word of words) {
    if (word.length !== pattern.length) { result.push(false); continue; }
    const forward = new Map();
    const backward = new Map();
    let ok = true;
    for (let i = 0; i < word.length; i++) {
      const a = pattern[i];
      const b = word[i];
      const x = forward.get(a);
      const y = backward.get(b);
      if (x === undefined && y === undefined) { forward.set(a, b); backward.set(b, a); }
      else if (x !== b || y !== a) { ok = false; break; }
    }
    result.push(ok);
  }
  return result;
}

function matchWords(pattern, words) { return solve(pattern, words); }

module.exports = solve;
module.exports.matchWords = matchWords;
