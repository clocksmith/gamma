"use strict";

function solve(street, k) {
  if (Array.isArray(street)) return street.length;
  while (!street.isDoorOpen()) {
    street.moveRight();
  }
  let ans = 0;
  for (let step = 1; step <= k; step++) {
    street.moveRight();
    if (street.isDoorOpen()) {
      ans = step;
      street.closeDoor();
    }
  }
  return ans;
}

function houseCount(street, k) {
  return solve(street, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.houseCount = houseCount;
