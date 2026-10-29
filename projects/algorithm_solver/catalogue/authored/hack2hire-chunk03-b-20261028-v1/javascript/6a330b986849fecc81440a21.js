"use strict";
// Hack2Hire 6a330b986849fecc81440a21 (Minimum Variant Conversion) over an INFERRED spec; qualification unknown.

function solve(product, k) {
  let ones = 0;
  for (const v of product) ones += v;
  if (ones === 0) return 0;
  let window = 0;
  for (let i = 0; i < k; i++) window += product[i];
  let smallest = window > 0 ? window : ones;
  for (let i = k; i < product.length; i++) {
    window += product[i] - product[i - k];
    if (window > 0 && window < smallest) smallest = window;
  }
  return ones + smallest * (smallest - 1) / 2;
}

function minimumConversionCost(product, k) { return solve(product, k); }

module.exports = solve;
module.exports.minimumConversionCost = minimumConversionCost;
