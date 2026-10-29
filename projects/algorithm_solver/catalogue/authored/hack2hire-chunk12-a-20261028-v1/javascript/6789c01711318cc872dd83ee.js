"use strict";
// Hack2Hire 6789c01711318cc872dd83ee (Longest Valid Parentheses) over an INFERRED spec; qualification unknown.

const RANK = {"(": 1, "[": 2, "{": 3, ")": 1, "]": 2, "}": 3};
const OPEN = {")": "(", "]": "[", "}": "{"};

function solve(s) {
  const pos = [], kind = [], inner = []; // open frames: position, opener, highest rank closed inside
  let barrier = -1, best = 0;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (!Object.hasOwn(OPEN, ch)) { pos.push(i); kind.push(ch); inner.push(0); }
    else if (kind.length && kind[kind.length - 1] === OPEN[ch] && inner[inner.length - 1] <= RANK[ch]) {
      pos.pop(); kind.pop(); inner.pop();
      let start;
      if (inner.length) { if (inner[inner.length - 1] < RANK[ch]) inner[inner.length - 1] = RANK[ch]; start = pos[pos.length - 1]; }
      else start = barrier;
      if (i - start > best) best = i - start;
    } else { pos.length = 0; kind.length = 0; inner.length = 0; barrier = i; }
  }
  return best;
}

function longestValidBrackets(s) { return solve(s); }

module.exports = solve;
module.exports.longestValidBrackets = longestValidBrackets;
