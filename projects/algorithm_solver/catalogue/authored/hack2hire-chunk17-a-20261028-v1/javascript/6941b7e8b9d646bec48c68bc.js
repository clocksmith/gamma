"use strict";
// Hack2Hire 6941b7e8b9d646bec48c68bc (String Tokenization) over an INFERRED spec; qualification unknown.

function solve(text, dictionary) {
  const root = {children: new Map(), id: null};
  for (const entry of dictionary) {
    const colon = entry.indexOf(":");
    const key = entry.slice(0, colon);
    let node = root;
    for (const ch of key) {
      let child = node.children.get(ch);
      if (child === undefined) { child = {children: new Map(), id: null}; node.children.set(ch, child); }
      node = child;
    }
    node.id = entry.slice(colon + 1);
  }
  const out = [];
  const n = text.length;
  let i = 0;
  while (i < n) {
    let node = root, j = i, best = null, bestEnd = i;
    while (j < n) {
      node = node.children.get(text[j]);
      if (node === undefined) break;
      j++;
      if (node.id !== null) { best = node.id; bestEnd = j; }
    }
    if (best === null) { out.push(text[i]); i++; }
    else { out.push(best); i = bestEnd; }
  }
  return out;
}

function tokenize(text, dictionary) { return solve(text, dictionary); }

module.exports = solve;
module.exports.tokenize = tokenize;
