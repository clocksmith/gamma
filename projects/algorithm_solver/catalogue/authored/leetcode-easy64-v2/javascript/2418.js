'use strict';

// 2418. Sort the People (Easy).
// Specification: https://leetcode.com/problems/sort-the-people/description/
// O(n log n) time, O(n) space; preserve both arrays; heights are distinct.
function solve(names, heights) {
  const order = Array.from({ length: names.length }, (_, index) => index);
  order.sort((left, right) => heights[right] - heights[left]);
  return order.map(index => names[index]);
}

const sortPeople = solve;
class Solution {
  sortPeople(names, heights) { return solve(names, heights); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortPeople };
