"use strict";
// Hack2Hire 67f8222b1d70a71460925c53 (Prefix Search II) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function solve(bizNames, searchWord) {
  const depth = searchWord.length, root = {kids: new Map(), hits: []};
  for (let index = 0; index < bizNames.length; index++) {
    const words = bizNames[index].split(" ");
    for (let position = 0; position < words.length; position++) {
      let node = root;
      for (const ch of words[position].slice(0, depth).toLowerCase()) {
        let child = node.kids.get(ch);
        if (child === undefined) { child = {kids: new Map(), hits: []}; node.kids.set(ch, child); }
        child.hits.push(index, position);
        node = child;
      }
    }
  }
  const out = [];
  let node = root;
  for (const ch of searchWord.toLowerCase()) {
    node = node === undefined ? undefined : node.kids.get(ch);
    if (node === undefined) { out.push([]); continue; }
    const first = new Map();
    for (let i = 0; i < node.hits.length; i += 2) {
      const index = node.hits[i], position = node.hits[i + 1], seen = first.get(index);
      if (seen === undefined || position < seen) first.set(index, position);
    }
    const keys = Array.from(first, ([index, position]) => [position, bizNames[index], index]);
    keys.sort((a, b) => a[0] - b[0] || cmp(a[1], b[1]) || a[2] - b[2]);
    out.push(keys.map((key) => key[1]));
  }
  return out;
}

function searchSuggestions(bizNames, searchWord) { return solve(bizNames, searchWord); }

module.exports = solve;
module.exports.searchSuggestions = searchSuggestions;
