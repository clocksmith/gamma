"use strict";
// Hack2Hire 6a4fae98665efda9311f5607 (Array Frequency Sort, variant 1) over an INFERRED spec; qualification unknown.
function solve(items) {
  const counts = new Map();
  for (const value of items) counts.set(value, (counts.get(value) || 0) + 1);
  const values = [...counts.keys()].sort((a, b) => counts.get(a) - counts.get(b) || a - b);
  const result = [];
  for (const value of values) for (let i = counts.get(value); i > 0; i--) result.push(value);
  return result;
}
function frequencySort(items) { return solve(items); }
module.exports = solve;
module.exports.frequencySort = frequencySort;
