"use strict";
// Hack2Hire 678ec4943d1b82777aa24f9a (Crypto Order Matching) over an INFERRED spec; qualification unknown.

class Heap {
  constructor(less, items = []) { this.a = items; this.less = less; for (let i = (items.length >> 1) - 1; i >= 0; i--) this.down(i); }
  get size() { return this.a.length; }
  peek() { return this.a[0]; }
  push(x) {
    const a = this.a; let i = a.length; a.push(x);
    while (i > 0) { const p = (i - 1) >> 1; if (!this.less(x, a[p])) break; a[i] = a[p]; i = p; }
    a[i] = x;
  }
  down(i) {
    const a = this.a, n = a.length, x = a[i];
    for (;;) {
      let c = 2 * i + 1;
      if (c >= n) break;
      if (c + 1 < n && this.less(a[c + 1], a[c])) c++;
      if (!this.less(a[c], x)) break;
      a[i] = a[c]; i = c;
    }
    a[i] = x;
  }
  pop() {
    const a = this.a, top = a[0], last = a.pop();
    if (a.length) { a[0] = last; this.down(0); }
    return top;
  }
}

function solve(buyPrices, sellPrices, orders) {
  const buys = new Heap((x, y) => x > y, buyPrices.slice());
  const sells = new Heap((x, y) => x < y, sellPrices.slice());
  const result = [];
  for (const [side, price] of orders) {
    if (side === "buy") {
      if (sells.size && sells.peek() <= price) result.push(sells.pop());
      else { buys.push(price); result.push(-1); }
    } else if (buys.size && buys.peek() >= price) result.push(buys.pop());
    else { sells.push(price); result.push(-1); }
  }
  return result;
}

function matchOrders(buyPrices, sellPrices, orders) { return solve(buyPrices, sellPrices, orders); }

module.exports = solve;
module.exports.matchOrders = matchOrders;
