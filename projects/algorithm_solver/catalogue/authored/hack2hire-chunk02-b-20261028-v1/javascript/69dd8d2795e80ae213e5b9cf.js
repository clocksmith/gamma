"use strict";
// Original Hack2Hire 69dd8d2795e80ae213e5b9cf native class variant over an INFERRED specification, with a separately declared trace adapter; qualification unknown.
function heapPush(heap, value) {
  heap.push(value);
  let i = heap.length - 1;
  while (i > 0) {
    const p = (i - 1) >> 1;
    if (heap[p] <= heap[i]) break;
    [heap[p], heap[i]] = [heap[i], heap[p]]; i = p;
  }
}
function heapPop(heap) {
  const top = heap[0], last = heap.pop();
  if (heap.length) {
    heap[0] = last;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let m = i;
      if (l < heap.length && heap[l] < heap[m]) m = l;
      if (r < heap.length && heap[r] < heap[m]) m = r;
      if (m === i) break;
      [heap[m], heap[i]] = [heap[i], heap[m]]; i = m;
    }
  }
  return top;
}
class ToDoList {
  constructor() { this.tasks = new Map(); this.requires = new Map(); this.edges = new Set(); }
  add(taskId, description, status) {
    if (!this.tasks.has(taskId)) { this.tasks.set(taskId, [taskId, description, status]); this.requires.set(taskId, []); }
  }
  get(taskId) { return this.tasks.has(taskId) ? [...this.tasks.get(taskId)] : []; }
  updateStatus(taskId, status) {
    if (!this.tasks.has(taskId)) return false;
    this.tasks.get(taskId)[2] = status;
    return true;
  }
  getDependencies(taskId) { return this.requires.has(taskId) ? [...this.requires.get(taskId)] : []; }
  reaches(start, target) {
    const seen = new Set([start]), stack = [start];
    while (stack.length) {
      const node = stack.pop();
      if (node === target) return true;
      for (const next of this.requires.get(node)) if (!seen.has(next)) { seen.add(next); stack.push(next); }
    }
    return false;
  }
  addDependency(taskId, dependsOnId) {
    const key = taskId + "\n" + dependsOnId;
    if (!this.tasks.has(taskId) || !this.tasks.has(dependsOnId) || taskId === dependsOnId || this.edges.has(key)) return false;
    if (this.reaches(dependsOnId, taskId)) return false;
    this.edges.add(key);
    this.requires.get(taskId).push(dependsOnId);
    return true;
  }
  getExecutionOrder() {
    const waiting = new Map(), dependents = new Map();
    for (const task of this.tasks.keys()) dependents.set(task, []);
    for (const [task, prerequisites] of this.requires) {
      waiting.set(task, prerequisites.length);
      for (const p of prerequisites) dependents.get(p).push(task);
    }
    const ready = [], order = [];
    for (const [task, count] of waiting) if (count === 0) heapPush(ready, task);
    while (ready.length) {
      const task = heapPop(ready);
      order.push(task);
      for (const d of dependents.get(task)) {
        waiting.set(d, waiting.get(d) - 1);
        if (waiting.get(d) === 0) heapPush(ready, d);
      }
    }
    return order;
  }
}
const METHODS = new Set(["add", "get", "updateStatus", "addDependency", "getDependencies", "getExecutionOrder"]);
function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ToDoList" || argumentLists[0].length !== 0) throw new Error("exact constructor required");
  const instance = new ToDoList(), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!METHODS.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.ToDoList = ToDoList;
