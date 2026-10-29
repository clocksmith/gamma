"use strict";
// Hack2Hire 69d1828717b72775cc49c028 (Nested String with Brackets Parsing, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(s) {
  const stack = [];
  let result = null, wordStart = -1;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (ch >= "a" && ch <= "z") { if (wordStart < 0) wordStart = i; continue; }
    if (wordStart >= 0) { stack[stack.length - 1].push(s.slice(wordStart, i)); wordStart = -1; }
    if (ch === "(") stack.push([]);
    else if (ch === ")") {
      const done = stack.pop();
      if (stack.length) stack[stack.length - 1].push(done); else result = done;
    }
  }
  return result;
}

function parseNested(s) { return solve(s); }

module.exports = solve;
module.exports.parseNested = parseNested;
