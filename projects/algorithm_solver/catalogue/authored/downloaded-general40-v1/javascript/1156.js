'use strict';

// 1156. Swap For Longest Repeated Character Substring (Medium).
// Specification: https://leetcode.com/problems/swap-for-longest-repeated-character-substring/description/
function solve(text) {
  const groups = [];
  for (let i = 0; i < text.length;) {
    let j = i;
    while (j < text.length && text[j] === text[i]) j++;
    groups.push([text[i], j - i]);
    i = j;
  }
  const total = {};
  for (const [ch, count] of groups) total[ch] = (total[ch] || 0) + count;
  let best = 0;
  for (const [ch, count] of groups) {
    best = Math.max(best, total[ch] > count ? count + 1 : count);
  }
  for (let i = 0; i + 2 < groups.length; i++) {
    if (groups[i][0] === groups[i + 2][0] && groups[i + 1][1] === 1) {
      const merged = groups[i][1] + groups[i + 2][1];
      best = Math.max(best, total[groups[i][0]] > merged ? merged + 1 : merged);
    }
  }
  return best;
}
const maxRepOpt1 = solve;
class Solution { maxRepOpt1(text) { return solve(text); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxRepOpt1 };
