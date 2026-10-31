"use strict";

function solve(mat, k) {
  const n = mat[0].length;
  const shift = k % n;
  if (shift === 0) return true;
  for (let i = 0; i < mat.length; i++) {
    const row = mat[i];
    for (let j = 0; j < n; j++) {
      if (row[j] !== row[(j + shift) % n]) return false;
    }
  }
  return true;
}

function areSimilar(mat, k) {
  return solve(mat, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.areSimilar = areSimilar;
