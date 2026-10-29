"use strict";
// Hack2Hire 69b785888a0eeb9897a8d23b (Car Fleet Scheduler, variant 2 of 2) over an INFERRED spec; qualification unknown.

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

function solve(leases, cars) {
  const order = leases.map((_, i) => i).sort((a, b) => leases[a][0] - leases[b][0] || a - b);
  const busy = new Heap((x, y) => x[0] < y[0] || (x[0] === y[0] && x[1] < y[1]));
  const ids = [];
  for (let c = 1; c <= cars; c++) ids.push(c);
  const free = new Heap((x, y) => x < y, ids);
  const result = new Array(leases.length).fill(0);
  for (const i of order) {
    const [start, end] = leases[i];
    while (busy.size && busy.peek()[0] <= start) free.push(busy.pop()[1]);
    if (free.size) {
      const car = free.pop();
      busy.push([end, car]);
      result[i] = car;
    } else {
      result[i] = -1;
    }
  }
  return result;
}

function assignCarsLimited(leases, cars) { return solve(leases, cars); }

module.exports = solve;
module.exports.assignCarsLimited = assignCarsLimited;
