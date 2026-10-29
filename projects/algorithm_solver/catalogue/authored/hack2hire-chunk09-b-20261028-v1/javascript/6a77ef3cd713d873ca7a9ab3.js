"use strict";
// Hack2Hire 6a77ef3cd713d873ca7a9ab3 (Count Incorrect Sale Prices) over an INFERRED spec; qualification unknown.

function solve(products, productPrices, productSold, soldPrice) {
  const correct = new Map();
  for (let i = 0; i < products.length; i++) correct.set(products[i], productPrices[i]);
  let wrong = 0;
  for (let j = 0; j < productSold.length; j++) if (correct.get(productSold[j]) !== soldPrice[j]) wrong++;
  return wrong;
}

function countIncorrect(products, productPrices, productSold, soldPrice) { return solve(products, productPrices, productSold, soldPrice); }

module.exports = solve;
module.exports.countIncorrect = countIncorrect;
