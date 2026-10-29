"use strict";

function solve(arr1, arr2, arr3) {
  let i = 0, j = 0, k = 0;
  const n1 = arr1.length, n2 = arr2.length, n3 = arr3.length;
  const res = [];
  while (i < n1 && j < n2 && k < n3) {
    const a = arr1[i], b = arr2[j], c = arr3[k];
    if (a === b && b === c) {
      res.push(a);
      i++; j++; k++;
    } else if (a <= b && a <= c) {
      i++;
    } else if (b <= a && b <= c) {
      j++;
    } else {
      k++;
    }
  }
  return res;
}

function arraysIntersection(arr1, arr2, arr3) {
  return solve(arr1, arr2, arr3);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.arraysIntersection = arraysIntersection;
