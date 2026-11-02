"use strict";

function solve(s) {
  const cnt = new Map();
  let left = 0, best = 0;
  for (let right = 0; right < s.length; right++) {
    const ch = s[right];
    cnt.set(ch, (cnt.get(ch) || 0) + 1);
    while (cnt.size > 2) {
      const lch = s[left++];
      const c = cnt.get(lch) - 1;
      if (c === 0) cnt.delete(lch);
      else cnt.set(lch, c);
    }
    if (right - left + 1 > best) best = right - left + 1;
  }
  return best;
}

function lengthOfLongestSubstringTwoDistinct(s) {
  return solve(s);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.lengthOfLongestSubstringTwoDistinct = lengthOfLongestSubstringTwoDistinct;
