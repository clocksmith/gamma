"use strict";
// Hack2Hire 67882811e20f8f324213c2a0 (Substring Wrapper) over an INFERRED spec; qualification unknown.

function solve(s, elements) {
  const children = [new Map()], terminal = [false];
  for (const e of elements) {
    let node = 0;
    for (const ch of e) {
      let next = children[node].get(ch);
      if (next === undefined) { next = children.length; children[node].set(ch, next); children.push(new Map()); terminal.push(false); }
      node = next;
    }
    terminal[node] = true;
  }
  const out = [];
  for (const word of s.split(" ")) {
    const n = word.length;
    let piece = word;
    for (let start = 0; start < n; start++) {
      let node = 0, best = 0;
      for (let p = start; p < n; p++) {
        node = children[node].get(word[p]);
        if (node === undefined) break;
        if (terminal[node]) best = p + 1 - start;
      }
      if (best) { piece = word.slice(0, start) + "[" + word.slice(start, start + best) + "]" + word.slice(start + best); break; }
    }
    out.push(piece);
  }
  return out.join(" ");
}

function wrapSubstrings(s, elements) { return solve(s, elements); }

module.exports = solve;
module.exports.wrapSubstrings = wrapSubstrings;
