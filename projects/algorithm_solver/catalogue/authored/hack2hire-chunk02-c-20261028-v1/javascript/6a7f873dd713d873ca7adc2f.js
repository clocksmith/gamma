"use strict";
// Hack2Hire 6a7f873dd713d873ca7adc2f (Balance Ads Across Columns, variant 1) over an INFERRED spec; qualification unknown.
function solve(heights) {
  const left = [], right = [];
  let leftTotal = 0, rightTotal = 0;
  heights.forEach((height, index) => {
    if (leftTotal <= rightTotal) { left.push(index); leftTotal += height; }
    else { right.push(index); rightTotal += height; }
  });
  return [left, right];
}
function assignColumns(heights) { return solve(heights); }
module.exports = solve;
module.exports.assignColumns = assignColumns;
