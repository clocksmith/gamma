"use strict";

const MP = { "0": "0", "1": "1", "6": "9", "8": "8", "9": "6" };

function solve(num) {
  let l = 0, r = num.length - 1;
  while (l <= r) {
    if (MP[num[l]] !== num[r]) return false;
    l++;
    r--;
  }
  return true;
}

function isStrobogrammatic(num) {
  return solve(num);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.isStrobogrammatic = isStrobogrammatic;
