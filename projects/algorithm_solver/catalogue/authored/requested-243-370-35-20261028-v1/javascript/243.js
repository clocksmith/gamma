"use strict";

function solve(wordsDict, word1, word2) {
  let i1 = -1, i2 = -1;
  let ans = wordsDict.length;
  for (let i = 0; i < wordsDict.length; i++) {
    const w = wordsDict[i];
    if (w === word1) {
      i1 = i;
      if (i2 !== -1 && i1 - i2 < ans) ans = i1 - i2;
    } else if (w === word2) {
      i2 = i;
      if (i1 !== -1 && i2 - i1 < ans) ans = i2 - i1;
    }
  }
  return ans;
}

function shortestDistance(wordsDict, word1, word2) {
  return solve(wordsDict, word1, word2);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.shortestDistance = shortestDistance;
