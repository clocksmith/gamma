"use strict";
// Hack2Hire 6796992ab10bc587828f27ae (Minimize Capital Gains Tax) over an INFERRED spec; qualification unknown.

// Max-heap of lots by price, with parallel arrays of prices and remaining amounts.
function solve(transactions) {
  const price = [];
  const amount = [];
  const swap = (i, j) => {
    const p = price[i]; price[i] = price[j]; price[j] = p;
    const a = amount[i]; amount[i] = amount[j]; amount[j] = a;
  };
  const push = (p, a) => {
    price.push(p); amount.push(a);
    let i = price.length - 1;
    while (i > 0) {
      const up = (i - 1) >> 1;
      if (price[up] >= price[i]) break;
      swap(up, i); i = up;
    }
  };
  const pop = () => {
    const end = price.length - 1;
    swap(0, end); price.pop(); amount.pop();
    let i = 0;
    const n = price.length;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let top = i;
      if (l < n && price[l] > price[top]) top = l;
      if (r < n && price[r] > price[top]) top = r;
      if (top === i) break;
      swap(i, top); i = top;
    }
  };
  let tenths = 0;
  for (const row of transactions) {
    let need = Number(row[2]);
    const p = Number(row[3]);
    if (row[1] === "buy") { push(p, need); continue; }
    let profit = 0;
    while (need > 0) {
      const have = amount[0];
      const take = need < have ? need : have;
      profit += (p - price[0]) * take;
      need -= take;
      if (take === have) pop(); else amount[0] = have - take;
    }
    if (profit > 0) tenths += profit;
  }
  return String(Math.floor(tenths / 10)) + "." + String(tenths % 10);
}

function minimizeTax(transactions) { return solve(transactions); }

module.exports = solve;
module.exports.minimizeTax = minimizeTax;
