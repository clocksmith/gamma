"use strict";

function solve(binaryMatrix) {
  let rows, cols, get;
  if (binaryMatrix && typeof binaryMatrix.dimensions === "function") {
    [rows, cols] = binaryMatrix.dimensions();
    get = (r, c) => binaryMatrix.get(r, c);
  } else {
    rows = binaryMatrix.length;
    cols = binaryMatrix[0].length;
    get = (r, c) => binaryMatrix[r][c];
  }
  let r = 0, c = cols - 1, ans = -1;
  while (r < rows && c >= 0) {
    if (get(r, c) === 1) {
      ans = c;
      c--;
    } else {
      r++;
    }
  }
  return ans;
}

function leftMostColumnWithOne(binaryMatrix) {
  return solve(binaryMatrix);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.leftMostColumnWithOne = leftMostColumnWithOne;
