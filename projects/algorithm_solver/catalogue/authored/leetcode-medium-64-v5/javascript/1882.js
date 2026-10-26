'use strict';

// 1882. Process Tasks Using Servers: separate available-server priority from completion-time priority.
// O((n + m) * log(n + 1)) time and O(n + m) space, with n servers and m tasks; inputs are read-only.
class MinHeap {
  constructor(before) {
    this.values = [];
    this.before = before;
  }

  get size() { return this.values.length; }

  peek() { return this.values[0]; }

  push(value) {
    const values = this.values;
    let index = values.length;
    values.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.before(value, values[parent])) break;
      values[index] = values[parent];
      index = parent;
    }
    values[index] = value;
  }

  pop() {
    const values = this.values;
    const result = values[0];
    const last = values.pop();
    if (values.length === 0) return result;
    let index = 0;
    while (2 * index + 1 < values.length) {
      let child = 2 * index + 1;
      if (child + 1 < values.length && this.before(values[child + 1], values[child])) child += 1;
      if (!this.before(values[child], last)) break;
      values[index] = values[child];
      index = child;
    }
    values[index] = last;
    return result;
  }
}

function solve(servers, tasks) {
  const available = new MinHeap((a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]));
  const busy = new MinHeap((a, b) => a[0] < b[0] ||
    (a[0] === b[0] && (a[1] < b[1] || (a[1] === b[1] && a[2] < b[2]))));
  for (let index = 0; index < servers.length; index += 1) available.push([servers[index], index]);
  const result = [];
  let time = 0;
  for (let arrival = 0; arrival < tasks.length; arrival += 1) {
    time = Math.max(time, arrival);
    if (!available.size && busy.peek()[0] > time) time = busy.peek()[0];
    while (busy.size && busy.peek()[0] <= time) {
      const [, weight, index] = busy.pop();
      available.push([weight, index]);
    }
    const [weight, index] = available.pop();
    result.push(index);
    busy.push([time + tasks[arrival], weight, index]);
  }
  return result;
}

const assignTasks = solve;
class Solution {
  assignTasks(servers, tasks) { return solve(servers, tasks); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, assignTasks };
