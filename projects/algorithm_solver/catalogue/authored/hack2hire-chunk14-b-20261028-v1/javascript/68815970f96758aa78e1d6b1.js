"use strict";
// Hack2Hire 68815970f96758aa78e1d6b1 (Wildcard Search) over an INFERRED spec; qualification unknown.

function find(text, piece, start) {
  const m = piece.length;
  if (m === 0) return start <= text.length ? start : -1;
  const fail = new Array(m).fill(0);
  for (let i = 1, k = 0; i < m; i++) {
    while (k && piece[i] !== piece[k]) k = fail[k - 1];
    if (piece[i] === piece[k]) k++;
    fail[i] = k;
  }
  for (let i = start, k = 0; i < text.length; i++) {
    while (k && text[i] !== piece[k]) k = fail[k - 1];
    if (text[i] === piece[k]) { k++; if (k === m) return i - m + 1; }
  }
  return -1;
}

function solve(pattern, str) {
  const pieces = pattern.split("*");
  const first = find(str, pieces[0], 0);
  if (first < 0 || pieces.length === 1) return first;
  let pos = first + pieces[0].length;
  for (let k = 1; k < pieces.length; k++) {
    const piece = pieces[k];
    if (!piece) continue;
    const at = find(str, piece, pos);
    if (at < 0) return -1;
    pos = at + piece.length;
  }
  return first;
}

function wildcardSearch(pattern, str) { return solve(pattern, str); }

module.exports = solve;
module.exports.wildcardSearch = wildcardSearch;
