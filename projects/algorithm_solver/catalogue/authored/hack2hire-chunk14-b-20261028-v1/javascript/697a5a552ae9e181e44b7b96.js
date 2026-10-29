"use strict";
// Hack2Hire 697a5a552ae9e181e44b7b96 (Worker-Task Matching with Specialties, variant 1 of 3) over an INFERRED spec; qualification unknown.

class Heap {
  constructor(less) { this.items = []; this.less = less; }
  get size() { return this.items.length; }
  top() { return this.items[0]; }
  push(x) {
    const a = this.items; a.push(x);
    let i = a.length - 1;
    while (i > 0) { const p = (i - 1) >> 1; if (!this.less(a[i], a[p])) break; [a[i], a[p]] = [a[p], a[i]]; i = p; }
  }
  pop() {
    const a = this.items, top = a[0], last = a.pop();
    if (a.length) {
      a[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1; let m = i;
        if (l < a.length && this.less(a[l], a[m])) m = l;
        if (r < a.length && this.less(a[r], a[m])) m = r;
        if (m === i) break;
        [a[i], a[m]] = [a[m], a[i]]; i = m;
      }
    }
    return top;
  }
}

const lessWorker = (x, y) => x[0] < y[0] || (x[0] === y[0] && x[1] < y[1]);

function solve(workers, tasks) {
  const heap = new Heap(lessWorker);
  workers.forEach((name, i) => heap.push([0, name, i]));
  const lists = workers.map(() => []);
  for (const [taskId, duration] of tasks) {
    const [load, name, i] = heap.pop();
    lists[i].push(taskId);
    heap.push([load + duration, name, i]);
  }
  return lists;
}

function assignTasks(workers, tasks) { return solve(workers, tasks); }

module.exports = solve;
module.exports.assignTasks = assignTasks;
