"use strict";
// Hack2Hire 6a9748740ca9cc4e1c789f00 (Autocorrect Prototype) over an INFERRED spec; qualification unknown.

function signature(s) {
  const codes = [];
  for (let i = 0; i < s.length; i++) codes.push(s.charCodeAt(i));
  codes.sort((a, b) => a - b);
  return String.fromCharCode(...codes);
}

function solve(words, queries) {
  const groups = new Map();
  for (const w of words) {
    const key = signature(w);
    const list = groups.get(key);
    if (list === undefined) groups.set(key, [w]); else list.push(w);
  }
  return queries.map((q) => (groups.get(signature(q)) || []).slice());
}

function findAnagrams(words, queries) { return solve(words, queries); }

module.exports = solve;
module.exports.findAnagrams = findAnagrams;
