"use strict";
// Hack2Hire 67df6ae706b62d81733ab893 (Merge Two Interval Lists) over an INFERRED spec; qualification unknown.

function solve(list1, list2) {
  const out = [];
  let i = 0, j = 0;
  while (i < list1.length || j < list2.length) {
    let start, end;
    if (j >= list2.length || (i < list1.length && list1[i][0] <= list2[j][0])) { [start, end] = list1[i]; i++; }
    else { [start, end] = list2[j]; j++; }
    if (out.length && start <= out[out.length - 1][1]) {
      if (end > out[out.length - 1][1]) out[out.length - 1][1] = end;
    } else out.push([start, end]);
  }
  return out;
}

function mergeIntervalLists(list1, list2) { return solve(list1, list2); }

module.exports = solve;
module.exports.mergeIntervalLists = mergeIntervalLists;
