'use strict';

// 3582. Generate Tag for Video Caption (Easy).
// Specification: https://leetcode.com/problems/generate-tag-for-video-caption/description/
// O(n) time and space; caption contains only English letters and spaces.
function solve(caption) {
  const words = caption.toLowerCase().split(' ').filter(word => word.length > 0);
  const parts = ['#'];
  for (let index = 0; index < words.length; index++) {
    const word = words[index];
    parts.push(index === 0 ? word : word[0].toUpperCase() + word.slice(1));
  }
  return parts.join('').slice(0, 100);
}

const generateTag = solve;
class Solution {
  generateTag(caption) { return solve(caption); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, generateTag };
