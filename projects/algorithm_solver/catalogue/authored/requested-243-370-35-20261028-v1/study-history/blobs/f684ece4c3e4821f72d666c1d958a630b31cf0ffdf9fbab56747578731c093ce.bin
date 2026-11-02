"use strict";

function solve(word) {
  const n = word.length;
  const total = 1 << n;
  const out = new Array(total);
  for (let mask = 0; mask < total; mask++) {
    let s = "";
    let cnt = 0;
    for (let i = 0; i < n; i++) {
      if ((mask >> i) & 1) {
        cnt++;
      } else {
        if (cnt > 0) {
          s += String(cnt);
          cnt = 0;
        }
        s += word[i];
      }
    }
    if (cnt > 0) s += String(cnt);
    out[mask] = s;
  }
  return out;
}

function generateAbbreviations(word) {
  return solve(word);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.generateAbbreviations = generateAbbreviations;
