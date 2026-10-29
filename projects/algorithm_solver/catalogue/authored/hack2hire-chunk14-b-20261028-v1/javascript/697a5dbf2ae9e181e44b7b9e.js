"use strict";
// Hack2Hire 697a5dbf2ae9e181e44b7b9e (Worker-Task Matching with Specialties, variant 3 of 3) over an INFERRED spec; qualification unknown.

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

function solve(workers, specialties, maxTasks, tasks, taskTypes) {
  const heaps = new Map(), version = new Array(workers.length).fill(0), load = new Array(workers.length).fill(0);
  workers.forEach((name, i) => {
    if (maxTasks[i] === 0) return;
    for (const kind of specialties[i]) {
      if (!heaps.has(kind)) heaps.set(kind, new Heap(lessWorker));
      heaps.get(kind).push([0, name, i, 0]);
    }
  });
  const lists = workers.map(() => []), left = [];
  tasks.forEach(([taskId, duration], t) => {
    const heap = heaps.get(taskTypes[t]);
    while (heap && heap.size && heap.top()[3] !== version[heap.top()[2]]) heap.pop();
    if (!heap || !heap.size) { left.push(taskId); return; }
    const i = heap.top()[2];
    lists[i].push(taskId);
    load[i] += duration;
    version[i]++;
    if (lists[i].length < maxTasks[i]) for (const other of specialties[i]) heaps.get(other).push([load[i], workers[i], i, version[i]]);
  });
  lists.push(left);
  return lists;
}

function assignTasksWithLimits(workers, specialties, maxTasks, tasks, taskTypes) { return solve(workers, specialties, maxTasks, tasks, taskTypes); }

module.exports = solve;
module.exports.assignTasksWithLimits = assignTasksWithLimits;
