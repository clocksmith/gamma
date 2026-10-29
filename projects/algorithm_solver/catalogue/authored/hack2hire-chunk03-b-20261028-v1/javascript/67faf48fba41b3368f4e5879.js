"use strict";
// Hack2Hire 67faf48fba41b3368f4e5879 (N-gram Split, level 2) over an INFERRED spec; qualification unknown.

function solve(text, ngrams) {
  const root = {children: new Map(), terminal: false};
  for (const entry of ngrams) {
    let node = root;
    for (const word of entry.split(' ')) {
      if (!node.children.has(word)) node.children.set(word, {children: new Map(), terminal: false});
      node = node.children.get(word);
    }
    node.terminal = true;
  }
  const words = text.split(' '), tokens = [];
  let i = 0;
  while (i < words.length) {
    let node = root, best = 1, j = i;
    while (j < words.length && node.children.has(words[j])) {
      node = node.children.get(words[j]);
      j++;
      if (node.terminal) best = j - i;
    }
    tokens.push(words.slice(i, i + best).join(' '));
    i += best;
  }
  return tokens;
}

function splitNgrams(text, ngrams) { return solve(text, ngrams); }

module.exports = solve;
module.exports.splitNgrams = splitNgrams;
