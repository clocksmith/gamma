"use strict";

function solve(prices) {
  const n = prices.length;
  const qIdx = new Int32Array(n + 2);
  const qVal = new Float64Array(n + 2);
  let head = 0;
  let tail = 0;
  qIdx[tail] = n + 1;
  qVal[tail] = 0;
  tail++;
  for (let i = n; i >= 1; i--) {
    while (head < tail && qIdx[head] > 2 * i + 1) head++;
    const cur = prices[i - 1] + qVal[head];
    while (head < tail && qVal[tail - 1] >= cur) tail--;
    qIdx[tail] = i;
    qVal[tail] = cur;
    tail++;
  }
  return qVal[tail - 1];
}

function minimumCoins(prices) {
  return solve(prices);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minimumCoins = minimumCoins;
