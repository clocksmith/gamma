"use strict";

function solve(word1, word2) {
  const n = word1.length, m = word2.length;
  const last = new Int32Array(m + 1).fill(-1);
  last[m] = n;
  let j = m - 1;
  for (let i = n - 1; i >= 0; i--) {
    if (j >= 0 && word1.charCodeAt(i) === word2.charCodeAt(j)) {
      last[j] = i;
      j--;
    }
  }
  const res = [];
  j = 0;
  let used = false;
  for (let i = 0; i < n && j < m; i++) {
    if (word1.charCodeAt(i) === word2.charCodeAt(j)) {
      res.push(i);
      j++;
    } else if (!used && last[j + 1] > i) {
      used = true;
      res.push(i);
      j++;
    }
  }
  return res.length === m ? res : [];
}

function validSequence(word1, word2) {
  return solve(word1, word2);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.validSequence = validSequence;
