"use strict";
// Hack2Hire 69a367fe6e73e4abccc9bfe1 (Next Consonant Transformation) over an INFERRED spec; qualification unknown.

const TABLE = (() => {
  const consonants = [];
  for (let c = 97; c < 123; c++) if (!"aeiou".includes(String.fromCharCode(c))) consonants.push(String.fromCharCode(c));
  const table = {};
  for (let c = 97; c < 123; c++) table[String.fromCharCode(c)] = String.fromCharCode(c);
  consonants.forEach((c, i) => { table[c] = consonants[(i + 1) % consonants.length]; });
  return table;
})();

function solve(s) {
  const out = new Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = TABLE[s[i]];
  return out.join("");
}

function transformString(s) { return solve(s); }

module.exports = solve;
module.exports.transformString = transformString;
