"use strict";
// Hack2Hire 6acfd3602e3a0349b3a8ec34 (Financial Account Ledger, variant 4 of 4) over an INFERRED spec; qualification unknown.

class MinHeap {
  constructor(less) { this.items = []; this.less = less; }
  get size() { return this.items.length; }
  peek() { return this.items[0]; }
  push(x) {
    const h = this.items; h.push(x);
    let i = h.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (!this.less(h[i], h[p])) break;
      [h[i], h[p]] = [h[p], h[i]]; i = p;
    }
  }
  pop() {
    const h = this.items, top = h[0], last = h.pop();
    if (h.length) {
      h[0] = last; let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1; let m = i;
        if (l < h.length && this.less(h[l], h[m])) m = l;
        if (r < h.length && this.less(h[r], h[m])) m = r;
        if (m === i) break;
        [h[i], h[m]] = [h[m], h[i]]; i = m;
      }
    }
    return top;
  }
}

function solve(commands) {
  const balance = new Map(), pending = new Map();
  const waiting = new Map(), stack = new Map();
  const out = [];
  let seq = 0;
  const settle = (account, day) => {
    const heap = pending.get(account);
    while (heap.size && heap.peek()[0] <= day) {
      const record = heap.pop()[2];
      if (!record[2]) {
        balance.set(account, balance.get(account) + record[0]);
        waiting.set(account, waiting.get(account) - record[0]);
      }
    }
  };
  for (const command of commands) {
    const f = command.split(" ");
    const kind = f[0];
    if (kind === "INIT") {
      balance.set(f[1], Number(f[2]));
      pending.set(f[1], new MinHeap((a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1])));
      waiting.set(f[1], 0); stack.set(f[1], []);
      continue;
    }
    const day = Number(f[1]), account = f[2];
    if (!balance.has(account)) {
      if (kind === "BALANCE" || kind === "PENDING") out.push(-1);
      continue;
    }
    settle(account, day);
    if (kind === "FUND") {
      const record = [Number(f[3]), day + Number(f[4]), false]; // amount, settle day, cancelled
      seq += 1;
      pending.get(account).push([record[1], seq, record]);
      waiting.set(account, waiting.get(account) + record[0]); stack.get(account).push(record);
    } else if (kind === "BALANCE") {
      out.push(balance.get(account));
    } else if (kind === "WITHDRAW") {
      const amount = Number(f[3]);
      if (amount <= balance.get(account)) balance.set(account, balance.get(account) - amount);
    } else if (kind === "TRANSFER") {
      const target = f[3], amount = Number(f[4]);
      if (balance.has(target) && target !== account && amount <= balance.get(account)) {
        balance.set(account, balance.get(account) - amount);
        balance.set(target, balance.get(target) + amount);
      }
    } else if (kind === "PENDING") {
      out.push(waiting.get(account));
    } else if (kind === "CANCEL") {
      const records = stack.get(account);
      while (records.length && (records[records.length - 1][2] || records[records.length - 1][1] <= day)) records.pop();
      if (records.length) {
        const record = records.pop();
        record[2] = true;
        waiting.set(account, waiting.get(account) - record[0]);
      }
    }
  }
  return out;
}

function processLedger(commands) { return solve(commands); }

module.exports = solve;
module.exports.processLedger = processLedger;
