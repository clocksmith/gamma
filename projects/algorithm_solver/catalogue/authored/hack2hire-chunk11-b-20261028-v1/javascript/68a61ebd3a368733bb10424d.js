"use strict";
// Hack2Hire 68a61ebd3a368733bb10424d (Incremental Task Scheduler) over an INFERRED spec; qualification unknown.

function heapPush(heap, item) {
  heap.push(item);
  let i = heap.length - 1;
  while (i > 0) {
    const p = (i - 1) >> 1;
    if (heap[p] <= item) break;
    heap[i] = heap[p]; i = p;
  }
  heap[i] = item;
}

function heapPop(heap) {
  const top = heap[0], last = heap.pop();
  if (heap.length > 0) {
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let m = i, best = last;
      if (l < heap.length && heap[l] < best) { m = l; best = heap[l]; }
      if (r < heap.length && heap[r] < best) { m = r; best = heap[r]; }
      if (m === i) break;
      heap[i] = heap[m]; i = m;
    }
    heap[i] = last;
  }
  return top;
}

class TaskScheduler {
  constructor() {
    this.prerequisites = new Map(); // added id -> its prerequisite list
    this.dependents = new Map();    // id (added or not) -> added tasks listing it
  }

  addTask(id, dependencies) {
    if (this.prerequisites.has(id)) return false;
    const wanted = new Set(dependencies);
    if (wanted.has(id)) return false;
    // a cycle appears exactly when a prerequisite already depends on id transitively
    const seen = new Set([id]), stack = [id];
    while (stack.length > 0) {
      const v = stack.pop(), next = this.dependents.get(v);
      if (next === undefined) continue;
      for (const w of next) {
        if (wanted.has(w)) return false;
        if (!seen.has(w)) { seen.add(w); stack.push(w); }
      }
    }
    this.prerequisites.set(id, dependencies.slice());
    for (const d of dependencies) {
      if (!this.dependents.has(d)) this.dependents.set(d, []);
      this.dependents.get(d).push(id);
    }
    return true;
  }

  getExecutionOrder() {
    const remaining = new Map(); // missing prerequisites never reach zero
    const heap = [];
    for (const [t, p] of this.prerequisites) { remaining.set(t, p.length); if (p.length === 0) heapPush(heap, t); }
    const order = [];
    while (heap.length > 0) {
      const t = heapPop(heap);
      order.push(t);
      const next = this.dependents.get(t);
      if (next === undefined) continue;
      for (const w of next) {
        const c = remaining.get(w) - 1;
        remaining.set(w, c);
        if (c === 0) heapPush(heap, w);
      }
    }
    return order;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "TaskScheduler" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new TaskScheduler(...argumentLists[0]);
  const allowed = new Set(["addTask", "getExecutionOrder"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.TaskScheduler = TaskScheduler;
