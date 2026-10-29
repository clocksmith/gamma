"use strict";
// Hack2Hire 6ab328bbe74ebb7457a3f0fc (Fault-Tolerant Work Queue, level 2) over an INFERRED spec; qualification unknown.

function heapLess(x, y) { return x[0] < y[0] || (x[0] === y[0] && x[1] < y[1]); }

function heapPush(heap, item) {
  heap.push(item);
  let i = heap.length - 1;
  while (i > 0) {
    const p = (i - 1) >> 1;
    if (!heapLess(heap[i], heap[p])) break;
    [heap[i], heap[p]] = [heap[p], heap[i]];
    i = p;
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
      if (l < heap.length && heapLess(heap[l], heap[m])) m = l;
      if (r < heap.length && heapLess(heap[r], heap[m])) m = r;
      if (m === i) break;
      [heap[i], heap[m]] = [heap[m], heap[i]];
      i = m;
    }
  }
  return top;
}

class WorkQueue {
  constructor(taskIds, dependencies, leaseDuration, maxAttempts) {
    this.lease = leaseDuration;
    this.cap = maxAttempts;
    this.position = new Map(taskIds.map((t, i) => [t, i]));
    this.attempts = new Map(taskIds.map((t) => [t, 0]));
    this.holder = new Map();
    this.heap = [];
    this.seq = 0;
    this.dead = [];
    this.deadSet = new Set();
    this.ready = [];
    this.readyHead = 0;
    this.dependents = new Map(taskIds.map((t) => [t, []]));
    this.missing = new Map(taskIds.map((t) => [t, 0]));
    for (const [before, after] of dependencies) {
      this.dependents.get(before).push(after);
      this.missing.set(after, this.missing.get(after) + 1);
    }
    for (const children of this.dependents.values()) children.sort((p, q) => this.position.get(p) - this.position.get(q));
    for (const t of taskIds) if (this.missing.get(t) === 0) this.ready.push(t);
  }

  release(task) {
    if (this.attempts.get(task) < this.cap) this.ready.push(task);
    else this.kill(task);
  }

  kill(task) {
    this.deadSet.add(task);
    this.dead.push(task);
    const frontier = [task];
    for (let head = 0; head < frontier.length; head++) {
      for (const child of this.dependents.get(frontier[head])) {
        if (!this.deadSet.has(child)) { this.deadSet.add(child); this.dead.push(child); frontier.push(child); }
      }
    }
  }

  expire(time) {
    while (this.heap.length && this.heap[0][0] <= time) {
      const [, seq, task] = heapPop(this.heap);
      if (this.holder.get(task) === seq) { this.holder.delete(task); this.release(task); }
    }
  }

  reserve(time) {
    this.expire(time);
    if (this.readyHead === this.ready.length) return -1;
    const task = this.ready[this.readyHead++];
    this.attempts.set(task, this.attempts.get(task) + 1);
    this.seq++;
    this.holder.set(task, this.seq);
    heapPush(this.heap, [time + this.lease, this.seq, task]);
    return task;
  }

  complete(time, taskId) {
    this.expire(time);
    if (!this.holder.has(taskId)) return false;
    this.holder.delete(taskId);
    const unlocked = [];
    for (const child of this.dependents.get(taskId)) {
      this.missing.set(child, this.missing.get(child) - 1);
      if (this.missing.get(child) === 0 && !this.deadSet.has(child)) unlocked.push(child);
    }
    unlocked.sort((p, q) => this.position.get(p) - this.position.get(q));
    for (const t of unlocked) this.ready.push(t);
    return true;
  }

  fail(time, taskId) {
    this.expire(time);
    if (!this.holder.has(taskId)) return false;
    this.holder.delete(taskId);
    this.release(taskId);
    return true;
  }

  getDeadLetters(time) {
    this.expire(time);
    return this.dead.slice();
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "WorkQueue" || argumentLists[0].length !== 4) throw new Error("exact initial constructor required");
  const instance = new WorkQueue(...argumentLists[0]);
  const allowed = new Set(["reserve", "complete", "fail", "getDeadLetters"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.WorkQueue = WorkQueue;
