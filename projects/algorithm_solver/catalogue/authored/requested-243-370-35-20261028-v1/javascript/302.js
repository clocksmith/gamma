"use strict";

function solve(image, x, y) {
  let rLo = x, rHi = x, cLo = y, cHi = y;
  for (let r = 0; r < image.length; r++) {
    const row = image[r];
    for (let c = 0; c < row.length; c++) {
      if (row[c] === "1" || row[c] === 1) {
        if (r < rLo) rLo = r;
        if (r > rHi) rHi = r;
        if (c < cLo) cLo = c;
        if (c > cHi) cHi = c;
      }
    }
  }
  return (rHi - rLo + 1) * (cHi - cLo + 1);
}

function minArea(image, x, y) {
  return solve(image, x, y);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minArea = minArea;
