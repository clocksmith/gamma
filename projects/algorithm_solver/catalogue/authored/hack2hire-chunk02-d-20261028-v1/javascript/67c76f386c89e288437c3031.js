"use strict";
// Hack2Hire 67c76f386c89e288437c3031 (Fill Equation with Operators) over an INFERRED spec; qualification unknown.

function solve(equation) {
  const [left, target] = equation.split(" = ");
  const nums = left.split(" ").map(Number);
  const goal = Number(target);
  const memo = new Map();
  // forms(i, j) -> [sums, products]; each entry [text, value]; a single atom counts as a product.
  function forms(i, j) {
    const key = i * 8 + j;
    if (memo.has(key)) return memo.get(key);
    let entry;
    if (i === j) entry = [[], [[String(nums[i]), nums[i]]]];
    else {
      const sums = [], products = [];
      for (let k = i; k < j; k++) {
        const heads = forms(i, k)[1];
        const [tailSums, tailProducts] = forms(k + 1, j);
        for (const [ht, hv] of heads) {
          for (const [tt, tv] of tailSums) sums.push([ht + "+" + tt, hv + tv]);
          for (const [tt, tv] of tailProducts) sums.push([ht + "+" + tt, hv + tv]);
        }
      }
      for (let k = i; k < j; k++) {
        const factors = forms(i, k)[0].map(([t, v]) => ["(" + t + ")", v]);
        if (k === i) factors.push([String(nums[i]), nums[i]]);
        const [tailSums, tailProducts] = forms(k + 1, j);
        const tails = tailSums.map(([t, v]) => ["(" + t + ")", v]).concat(tailProducts);
        for (const [ft, fv] of factors) for (const [tt, tv] of tails) products.push([ft + "*" + tt, fv * tv]);
      }
      entry = [sums, products];
    }
    memo.set(key, entry);
    return entry;
  }
  const [sums, products] = forms(0, nums.length - 1);
  const found = new Set();
  for (const [text, value] of sums.concat(products)) if (value === goal) found.add(text);
  return [...found].sort();
}

function fillOperators(equation) { return solve(equation); }

module.exports = solve;
module.exports.fillOperators = fillOperators;
