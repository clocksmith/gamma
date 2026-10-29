"use strict";
// Hack2Hire 688bd40e3867670cfb894186 (String Replacement) over an INFERRED spec; qualification unknown.

function solve(source, target, replacement) {
  const m = target.length, fail = new Int32Array(m);
  for (let i = 1, k = 0; i < m; i++) {
    while (k && target[i] !== target[k]) k = fail[k - 1];
    if (target[i] === target[k]) k++;
    fail[i] = k;
  }
  const starts = [];
  for (let i = 0, k = 0; i < source.length; i++) {
    const ch = source[i];
    while (k && ch !== target[k]) k = fail[k - 1];
    if (ch === target[k]) k++;
    if (k === m) { starts.push(i - m + 1); k = 0; }
  }
  const out = [];
  for (let i = 0, next = 0; i < source.length;) {
    if (next < starts.length && starts[next] === i) { out.push(replacement); i += m; next++; }
    else out.push(source[i++]);
  }
  return out.join("");
}

function replaceAll(source, target, replacement) { return solve(source, target, replacement); }

module.exports = solve;
module.exports.replaceAll = replaceAll;
