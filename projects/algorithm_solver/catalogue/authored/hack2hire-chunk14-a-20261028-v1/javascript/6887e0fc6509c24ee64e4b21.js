"use strict";
// Hack2Hire 6887e0fc6509c24ee64e4b21 (String Reorganization) over an INFERRED spec; qualification unknown.

function solve(s) {
  const counts = new Array(26).fill(0);
  for (let i = 0; i < s.length; i++) counts[s.charCodeAt(i) - 97] += 1;
  const n = s.length;
  if (Math.max(...counts) > Math.floor((n + 1) / 2)) return "";
  const out = [];
  let previous = -1, lowest = 0, remaining = n;
  for (let step = 0; step < n; step++) {
    while (counts[lowest] === 0) lowest += 1;
    let top = 0, holders = 0;
    for (let c = lowest; c < 26; c++) {
      if (counts[c] > top) { top = counts[c]; holders = 1; } else if (counts[c] === top) holders += 1;
    }
    const after = remaining - 1;
    const half = Math.floor((after + 1) / 2);
    for (let c = lowest; c < 26; c++) {
      if (c === previous || counts[c] === 0) continue;
      const newTop = counts[c] === top && holders === 1 ? top - 1 : top;
      const leftC = counts[c] - 1;
      if (newTop <= half && !(after % 2 === 1 && leftC === half)) {
        counts[c] = leftC;
        out.push(String.fromCharCode(97 + c));
        previous = c;
        remaining = after;
        break;
      }
    }
  }
  return out.join("");
}

function reorganize(s) { return solve(s); }

module.exports = solve;
module.exports.reorganize = reorganize;
