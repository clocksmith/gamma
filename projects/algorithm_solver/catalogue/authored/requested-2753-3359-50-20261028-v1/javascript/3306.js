"use strict";

function isVowel(ch) {
  return ch === "a" || ch === "e" || ch === "i" || ch === "o" || ch === "u";
}

function solve(word, k) {
  function atLeast(limit) {
    const vcnt = new Map();
    let cons = 0;
    let left = 0;
    let ans = 0;
    const n = word.length;
    for (let right = 0; right < n; right++) {
      const ch = word[right];
      if (isVowel(ch)) vcnt.set(ch, (vcnt.get(ch) || 0) + 1);
      else cons++;
      while (vcnt.size === 5 && cons >= limit) {
        ans += n - right;
        const lch = word[left++];
        if (isVowel(lch)) {
          const c = vcnt.get(lch) - 1;
          if (c === 0) vcnt.delete(lch);
          else vcnt.set(lch, c);
        } else {
          cons--;
        }
      }
    }
    return ans;
  }
  return atLeast(k) - atLeast(k + 1);
}

function countOfSubstrings(word, k) {
  return solve(word, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.countOfSubstrings = countOfSubstrings;
