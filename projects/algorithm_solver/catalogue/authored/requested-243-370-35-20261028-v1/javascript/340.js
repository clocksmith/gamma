"use strict";

function solve(s, k) {
  if (k === 0) return 0;
  const cnt = new Map();
  let left = 0;
  let best = 0;
  for (let right = 0; right < s.length; right++) {
    const ch = s[right];
    cnt.set(ch, (cnt.get(ch) || 0) + 1);
    while (cnt.size > k) {
      const lch = s[left++];
      const c = cnt.get(lch) - 1;
      if (c === 0) cnt.delete(lch);
      else cnt.set(lch, c);
    }
    if (right - left + 1 > best) best = right - left + 1;
  }
  return best;
}

function lengthOfLongestSubstringKDistinct(s, k) {
  return solve(s, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.lengthOfLongestSubstringKDistinct = lengthOfLongestSubstringKDistinct;
