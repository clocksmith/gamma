'use strict';

// 4007. Widest Possible Fence.
// Specification: https://leetcode.com/problems/widest-possible-fence/description/
// O(n+u^2) expected time and O(u^2) space; positive heights keep singles disjoint from complementary pairs. Inputs are preserved.
function solve(planks) {
  const counts = new Map();
  for (const height of planks) counts.set(height, (counts.get(height) || 0) + 1);
  const heights = [...counts.keys()];
  const widths = new Map(counts);
  let answer = 1;
  for (const count of counts.values()) answer = Math.max(answer, count);
  for (let first = 0; first < heights.length; first++) {
    for (let second = first; second < heights.length; second++) {
      const left = heights[first];
      const right = heights[second];
      const pairs = first === second ? Math.floor(counts.get(left) / 2) : Math.min(counts.get(left), counts.get(right));
      const height = left + right;
      const width = (widths.get(height) || 0) + pairs;
      widths.set(height, width);
      answer = Math.max(answer, width);
    }
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
