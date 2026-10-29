"use strict";
// Hack2Hire 677b5f4078175fce2ecdfc13 (End Of Day Balance, variant 2 of 2) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

// Binary min-heap of party ranks in an Int32Array, ordered by key[rank], then rank (rank order == name order).
// Comparisons are inlined so the heap stays fast under node --jitless.
class Heap {
  constructor(key, items) {
    this.key = key; this.a = Int32Array.from(items); this.n = items.length;
    for (let i = (this.n >> 1) - 1; i >= 0; i--) this.down(i);
  }
  get size() { return this.n; }
  push(x) {
    const a = this.a, key = this.key, kx = key[x];
    let i = this.n++;
    while (i > 0) {
      const p = (i - 1) >> 1, y = a[p], ky = key[y];
      if (kx > ky || (kx === ky && x > y)) break;
      a[i] = y; i = p;
    }
    a[i] = x;
  }
  pop() {
    const a = this.a, top = a[0];
    this.n--;
    if (this.n > 0) { a[0] = a[this.n]; this.down(0); }
    return top;
  }
  down(i) {
    const a = this.a, key = this.key, n = this.n, x = a[i], kx = key[x];
    for (;;) {
      let c = 2 * i + 1;
      if (c >= n) break;
      let y = a[c], ky = key[y];
      if (c + 1 < n) {
        const z = a[c + 1], kz = key[z];
        if (kz < ky || (kz === ky && z < y)) { c++; y = z; ky = kz; }
      }
      if (kx < ky || (kx === ky && x < y)) break;
      a[i] = y; i = c;
    }
    a[i] = x;
  }
}

function solve(transactions) {
  const balance = new Map();
  for (const [payer, payee, amount] of transactions) {
    balance.set(payer, (balance.get(payer) || 0) - amount);
    balance.set(payee, (balance.get(payee) || 0) + amount);
  }
  const names = Array.from(balance.keys()).sort(cmp), key = new Float64Array(names.length);
  const credit = [], debt = [];
  for (let rank = 0; rank < names.length; rank++) {
    const value = balance.get(names[rank]);
    key[rank] = -Math.abs(value);  // both heaps pop the largest open amount first
    if (value > 0) credit.push(rank);
    else if (value < 0) debt.push(rank);
  }
  const creditors = new Heap(key, credit), debtors = new Heap(key, debt), transfers = [];
  while (creditors.size) {
    const creditor = creditors.pop(), debtor = debtors.pop();
    const amount = Math.min(-key[creditor], -key[debtor]);
    transfers.push([names[debtor], names[creditor], amount]);
    key[creditor] += amount; key[debtor] += amount;
    if (key[creditor] < 0) creditors.push(creditor);
    if (key[debtor] < 0) debtors.push(debtor);
  }
  return transfers;
}

function settleBalances(transactions) { return solve(transactions); }

module.exports = solve;
module.exports.settleBalances = settleBalances;
