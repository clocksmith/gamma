"use strict";
// Hack2Hire 69efc96396981f58ae1f6d77 (Design a Task Assignment System, variant 4 of 4) over an INFERRED spec; qualification unknown.

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

function byName(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

class TaskManager {
  constructor() {
    this.tasks = new Map(); // taskId -> [name, priority, creation number]
    this.count = 0;
    this.users = new Map(); this.seq = 0;
  }

  addTask(timestamp, name, priority) {
    this.count += 1;
    const taskId = "taskId" + this.count;
    this.tasks.set(taskId, [name, priority, this.count]);
    return taskId;
  }

  updateTask(timestamp, taskId, name, priority) {
    const task = this.tasks.get(taskId);
    if (task === undefined) return false;
    task[0] = name; task[1] = priority;
    return true;
  }

  getTask(timestamp, taskId) {
    const task = this.tasks.get(taskId);
    return task === undefined ? "" : `${task[0]}(${task[1]})`;
  }

  ordered(nameFilter, limit) {
    const picked = [];
    for (const [id, t] of this.tasks) if (nameFilter === null || t[0].includes(nameFilter)) picked.push([t[1], t[2], id]);
    picked.sort((a, b) => b[0] - a[0] || a[1] - b[1]);
    return picked.slice(0, limit).map((x) => x[2]);
  }

  searchTasks(timestamp, nameFilter, maxResults) { return this.ordered(nameFilter, maxResults); }

  listTasksSorted(timestamp, limit) { return this.ordered(null, limit); }

  user(userId, now) {
    const user = this.users.get(userId);
    if (user !== undefined) {
      while (user.heap.size && user.heap.peek()[0] <= now) {
        const [, seq, taskId] = user.heap.pop();
        const entry = user.active.get(taskId);
        if (entry !== undefined && entry[1] === seq) { user.active.delete(taskId); user.overdue.push([seq, taskId]); }
      }
    }
    return user;
  }

  addUser(timestamp, userId, quota) {
    if (this.users.has(userId)) return false;
    this.users.set(userId, {quota, active: new Map(), heap: new MinHeap((a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1])), overdue: []});
    return true;
  }

  assignTask(timestamp, taskId, userId, finishTime) {
    const user = this.user(userId, timestamp);
    if (user === undefined || !this.tasks.has(taskId)) return false;
    if (user.active.has(taskId) || user.active.size >= user.quota) return false;
    this.seq += 1;
    user.active.set(taskId, [finishTime, this.seq]);
    user.heap.push([finishTime, this.seq, taskId]);
    return true;
  }

  getUserTasks(timestamp, userId) {
    const user = this.user(userId, timestamp);
    if (user === undefined) return [];
    const rows = [];
    for (const [taskId, [f, s]] of user.active) rows.push([f, s, taskId]);
    rows.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    return rows.map((r) => r[2]);
  }

  completeTask(timestamp, taskId, userId) {
    const user = this.user(userId, timestamp);
    return user !== undefined && user.active.delete(taskId);
  }

  getOverdueAssignments(timestamp, userId) {
    const user = this.user(userId, timestamp);
    if (user === undefined) return [];
    return user.overdue.slice().sort((a, b) => a[0] - b[0]).map((x) => x[1]);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "TaskManager" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new TaskManager(...argumentLists[0]);
  const allowed = new Set(["addTask", "updateTask", "getTask", "searchTasks", "listTasksSorted", "addUser", "assignTask", "getUserTasks", "completeTask", "getOverdueAssignments"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.TaskManager = TaskManager;
