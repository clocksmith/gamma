"use strict";
// Hack2Hire 67d2675b5e44a1b0c201ee7a (Margin Call, level 2) over an INFERRED spec; qualification unknown.

const LEVEL = 2;

function solve(trades) {
  let cash = 1000;
  const held = new Map(), price = new Map(), heap = [];  // heap of [-price, symbol]
  const less = (a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);
  function heapPush(item) {
    heap.push(item);
    let i = heap.length - 1;
    while (i > 0) {
      const parent = (i - 1) >> 1;
      if (!less(heap[i], heap[parent])) break;
      const t = heap[i]; heap[i] = heap[parent]; heap[parent] = t; i = parent;
    }
  }
  function heapPop() {
    const last = heap.pop();
    if (!heap.length) return;
    heap[0] = last;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let m = i;
      if (l < heap.length && less(heap[l], heap[m])) m = l;
      if (r < heap.length && less(heap[r], heap[m])) m = r;
      if (m === i) break;
      const t = heap[i]; heap[i] = heap[m]; heap[m] = t; i = m;
    }
  }
  const qty = (sym) => held.get(sym) || 0;
  function sellable(sym) {
    const q = qty(sym);
    if (LEVEL < 3 || sym.endsWith("O")) return q;
    return Math.max(0, q - qty(sym + "O"));
  }
  function push(sym) { if (price.has(sym)) heapPush([-price.get(sym), sym]); }
  function change(sym, delta) {
    const q = qty(sym) + delta;
    if (q) held.set(sym, q); else held.delete(sym);
  }
  function marginCall() {
    while (cash < 0) {
      while (heap.length && (price.get(heap[0][1]) !== -heap[0][0] || sellable(heap[0][1]) === 0)) heapPop();
      if (!heap.length) break;
      const sym = heap[0][1], p = price.get(sym), deficit = -cash;
      const base = LEVEL === 3 && sym.endsWith("O") ? sym.slice(0, -1) : null;
      if (base !== null && held.has(base) && price.get(base) >= p) {
        const pb = price.get(base), qu = held.get(base);
        let qx = held.get(sym);
        const n = Math.min(Math.max(0, qx - qu), Math.floor((deficit + p - 1) / p));
        cash += n * p; change(sym, -n); qx -= n;
        if (cash < 0 && qx) {
          const pairs = Math.floor((-cash - 1) / (p + pb));
          if (pairs >= qx) {
            cash += qx * (p + pb); change(sym, -qx); change(base, -qx);
          } else {
            cash += pairs * (p + pb) + p; change(sym, -pairs - 1); change(base, -pairs);
            if (cash < 0) { cash += pb; change(base, -1); }
          }
        }
        push(base);
      } else {
        const n = Math.min(sellable(sym), Math.floor((deficit + p - 1) / p));
        cash += n * p; change(sym, -n);
        if (base !== null) push(base);
      }
    }
  }
  for (const trade of trades) {
    const sym = trade[1], q0 = Number(trade[3]), p = Number(trade[4]);
    price.set(sym, p);
    if (trade[2] === "B") { cash -= q0 * p; change(sym, q0); }
    else { const q = Math.min(q0, qty(sym)); cash += q * p; change(sym, -q); }
    if (LEVEL >= 2) {
      push(sym);
      if (LEVEL === 3 && sym.endsWith("O")) push(sym.slice(0, -1));
      if (cash < 0) marginCall();
    }
  }
  const out = [["CASH", String(cash)]];
  for (const sym of [...held.keys()].sort()) out.push([sym, String(held.get(sym))]);
  return out;
}

function marginCall(trades) { return solve(trades); }

module.exports = solve;
module.exports.marginCall = marginCall;
