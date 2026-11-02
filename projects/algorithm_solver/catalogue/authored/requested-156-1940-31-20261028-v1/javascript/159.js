"use strict";

// string_unit = unicode_codepoint: a non-BMP character is one unit, matching
// Python str and the reference. The Array.from copy is charged as O(n) space.
function solve(s) {
  const chars = Array.from(s);
  const cnt = new Map();
  let left = 0, best = 0;
  for (let right = 0; right < chars.length; right++) {
    const ch = chars[right];
    cnt.set(ch, (cnt.get(ch) || 0) + 1);
    while (cnt.size > 2) {
      const lch = chars[left++];
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
if (typeof Solution !== "undefined") solve.Solution = Solution;
