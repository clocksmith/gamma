"use strict";
// Hack2Hire 67a922ffea201244f8fae261 (Longest Prefix And Suffix) over an INFERRED spec; qualification unknown.

function solve(s) {
  const n = s.length;
  const pi = new Int32Array(n);
  let k = 0;
  for (let i = 1; i < n; i++) {
    while (k && s.charCodeAt(i) !== s.charCodeAt(k)) k = pi[k - 1];
    if (s.charCodeAt(i) === s.charCodeAt(k)) k++;
    pi[i] = k;
  }
  return pi[n - 1];
}

function longestPrefixSuffix(s) { return solve(s); }

module.exports = solve;
module.exports.longestPrefixSuffix = longestPrefixSuffix;
