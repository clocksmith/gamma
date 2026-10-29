"use strict";

function solve(words, s) {
  const n = s.length;
  const bold = new Uint8Array(n);
  for (let i = 0; i < words.length; i++) {
    const w = words[i];
    const L = w.length;
    let start = s.indexOf(w);
    while (start !== -1) {
      for (let j = start; j < start + L; j++) bold[j] = 1;
      start = s.indexOf(w, start + 1);
    }
  }
  let out = "";
  for (let i = 0; i < n; i++) {
    if (bold[i] && (i === 0 || !bold[i - 1])) out += "<b>";
    out += s[i];
    if (bold[i] && (i === n - 1 || !bold[i + 1])) out += "</b>";
  }
  return out;
}

function boldWords(words, s) {
  return solve(words, s);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.boldWords = boldWords;
