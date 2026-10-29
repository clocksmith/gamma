"use strict";
// Hack2Hire 6763722dcc8f5deed53ccd73 (Bank Service Maximization) over an INFERRED spec; qualification unknown.

function solve(initialBalance, transactions) {
  const n = transactions.length, prefix = new Array(n + 1).fill(0);
  for (let k = 0; k < n; k++) prefix[k + 1] = prefix[k] + transactions[k];
  const stack = [n];  // prefix values increase from bottom to top
  let best = 0;
  for (let s = n - 1; s >= 0; s--) {
    const limit = prefix[s] - initialBalance;
    let lo = 0, hi = stack.length;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (prefix[stack[mid]] < limit) lo = mid + 1; else hi = mid; }
    const served = lo === 0 ? n - s : stack[lo - 1] - 1 - s;
    if (served > best) best = served;
    while (stack.length && prefix[stack[stack.length - 1]] >= prefix[s]) stack.pop();
    stack.push(s);
  }
  return best;
}

function maxCustomersServed(initialBalance, transactions) { return solve(initialBalance, transactions); }

module.exports = solve;
module.exports.maxCustomersServed = maxCustomersServed;
