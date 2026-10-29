"use strict";
// Hack2Hire 677ed3ec052a260e0165706f (Design Delayed Tasks Scheduler) over an INFERRED spec; qualification unknown.

class MinHeap {
  // entries are arrays compared element-wise on their first two (numeric) fields
  constructor() { this.items = []; }
  get size() { return this.items.length; }
  static less(a, b) { return a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]); }
  push(x) {
    const h = this.items; h.push(x);
    let i = h.length - 1;
    while (i > 0) { const p = (i - 1) >> 1; if (!MinHeap.less(h[i], h[p])) break; [h[i], h[p]] = [h[p], h[i]]; i = p; }
  }
  peek() { return this.items[0]; }
  pop() {
    const h = this.items, top = h[0], last = h.pop();
    if (h.length) {
      h[0] = last; let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1; let m = i;
        if (l < h.length && MinHeap.less(h[l], h[m])) m = l;
        if (r < h.length && MinHeap.less(h[r], h[m])) m = r;
        if (m === i) break;
        [h[i], h[m]] = [h[m], h[i]]; i = m;
      }
    }
    return top;
  }
}

class DelayedTaskScheduler {
  constructor() { this.heap = new MinHeap(); this.pending = new Map(); this.seq = 0; } // heap of [run time, sequence, id]

  schedule(taskId, delayTime, currentTime) {
    this.seq += 1;
    const runAt = currentTime + delayTime;
    this.pending.set(taskId, this.seq);
    this.heap.push([runAt, this.seq, taskId]);
    return runAt;
  }

  runDue(currentTime) {
    const done = [];
    while (this.heap.size && this.heap.peek()[0] <= currentTime) {
      const [, seq, task] = this.heap.pop();
      if (this.pending.get(task) === seq) { this.pending.delete(task); done.push(task); }
    }
    return done;
  }

  cancel(taskId) { return this.pending.delete(taskId); } // its heap entry becomes stale
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "DelayedTaskScheduler" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new DelayedTaskScheduler(...argumentLists[0]);
  const allowed = new Set(["schedule", "runDue", "cancel"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.DelayedTaskScheduler = DelayedTaskScheduler;
