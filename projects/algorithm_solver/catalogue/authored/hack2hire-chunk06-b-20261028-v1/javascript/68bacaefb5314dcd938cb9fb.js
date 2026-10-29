"use strict";
// Hack2Hire 68bacaefb5314dcd938cb9fb (Highlight Phrases in Review) over an INFERRED spec; qualification unknown.

const isAlnum = (code) => (code >= 48 && code <= 57) || (code >= 65 && code <= 90) || (code >= 97 && code <= 122);

function solve(review, mapping) {
  const trie = [new Map()], category = [null];
  for (const [phrase, cat] of mapping) {
    let node = 0;
    for (const ch of phrase.toLowerCase()) {
      let nxt = trie[node].get(ch);
      if (nxt === undefined) { nxt = trie.length; trie[node].set(ch, nxt); trie.push(new Map()); category.push(null); }
      node = nxt;
    }
    if (category[node] === null) category[node] = cat;
  }
  const low = review.toLowerCase(), n = review.length, out = [];
  let i = 0, copyFrom = 0;
  while (i < n) {
    if (isAlnum(review.charCodeAt(i)) && (i === 0 || !isAlnum(review.charCodeAt(i - 1)))) {
      let node = 0, j = i, best = -1, bestCat = null;
      while (j < n) {
        node = trie[node].get(low[j]);
        if (node === undefined) break;
        j++;
        if (category[node] !== null && (j === n || !isAlnum(review.charCodeAt(j)))) { best = j; bestCat = category[node]; }
      }
      if (best >= 0) {
        out.push(review.slice(copyFrom, i), "[" + bestCat + "]{" + review.slice(i, best) + "}");
        i = best; copyFrom = best;
        continue;
      }
    }
    i++;
  }
  out.push(review.slice(copyFrom));
  return out.join("");
}

function highlightReview(review, mapping) { return solve(review, mapping); }

module.exports = solve;
module.exports.highlightReview = highlightReview;
