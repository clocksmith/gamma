"use strict";
// Hack2Hire 6800861ac48db1937ce88f5d (Merge Common Substring) over an INFERRED spec; qualification unknown.

function solve(str1, str2) {
  const m = Math.min(str1.length, str2.length);
  const text = str2 + '#' + str1.slice(str1.length - m);
  const pi = new Int32Array(text.length);
  let k = 0;
  for (let i = 1; i < text.length; i++) {
    while (k && text.charCodeAt(i) !== text.charCodeAt(k)) k = pi[k - 1];
    if (text.charCodeAt(i) === text.charCodeAt(k)) k++;
    pi[i] = k;
  }
  return str1 + str2.slice(pi[text.length - 1]);
}

function mergeCommonSubstring(str1, str2) { return solve(str1, str2); }

module.exports = solve;
module.exports.mergeCommonSubstring = mergeCommonSubstring;
