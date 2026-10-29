"use strict";
// Hack2Hire 67cd24763363b83a81fc99af (Check Password Similarity) over an INFERRED spec; qualification unknown.

function similar(next, old) {
  let j = 0;
  const m = old.length;
  for (let i = 0; i < next.length && j < m; i++) {
    const c = next.charCodeAt(i);
    const successor = c === 122 ? 97 : c + 1;
    const want = old.charCodeAt(j);
    if (want === c || want === successor) j++;
  }
  return j === m;
}

function solve(newPasswords, oldPasswords) {
  return newPasswords.map((next, i) => (similar(next, oldPasswords[i]) ? "YES" : "NO"));
}

function checkSimilarity(newPasswords, oldPasswords) { return solve(newPasswords, oldPasswords); }

module.exports = solve;
module.exports.checkSimilarity = checkSimilarity;
