'use strict';

// 760. Find Anagram Mappings (Easy).
// Specification: https://leetcode.com/problems/find-anagram-mappings/description/
function solve(nums1, nums2) {
  const indexByValue = new Map();
  for (let i = 0; i < nums2.length; i++) indexByValue.set(nums2[i], i);
  return nums1.map((value) => indexByValue.get(value));
}
const anagramMappings = solve;
class Solution { anagramMappings(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, anagramMappings };
