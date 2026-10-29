// Original hack2hire:6764932ccc8f5deed53ccd76; inferred public-preview contract; qualification unknown.
"use strict";
function isValidDate(a, b, c) {
  for (const [year, month, day] of [[a,b,c], [a,c,b], [b,a,c], [b,c,a], [c,a,b], [c,b,a]]) {
    if (year < 1 || year > 9999 || month < 1 || month > 12 || day < 1) continue;
    const leap = year % 400 === 0 || year % 4 === 0 && year % 100 !== 0;
    const lengths = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if (day <= lengths[month - 1]) return true;
  }
  return false;
}

const solve = isValidDate;
module.exports = solve;
module.exports.isValidDate = isValidDate;
module.exports.Solution = class { isValidDate(...args) { return isValidDate(...args); } };
