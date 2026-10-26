'use strict';

// 2402. Meeting Rooms III. Separate heaps for available rooms and their finishing times; O(m log m+(m+n) log(n+1)) time and O(m+n) space. Inputs are preserved.

class MinHeap {
  constructor(less) {
    this.items = [];
    this.less = less;
  }

  get size() { return this.items.length; }
  peek() { return this.items[0]; }

  push(value) {
    const items = this.items;
    let index = items.length;
    items.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.less(value, items[parent])) break;
      items[index] = items[parent];
      index = parent;
    }
    items[index] = value;
  }

  pop() {
    const items = this.items;
    const result = items[0];
    const value = items.pop();
    if (items.length === 0) return result;
    let index = 0;
    while (2 * index + 1 < items.length) {
      let child = 2 * index + 1;
      if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
      if (!this.less(items[child], value)) break;
      items[index] = items[child];
      index = child;
    }
    items[index] = value;
    return result;
  }
}

function solve(n, meetings) {
  const available = new MinHeap((a, b) => a < b);
  const busy = new MinHeap((a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]));
  const counts = Array(n).fill(0);
  for (let room = 0; room < n; room += 1) available.push(room);
  for (const [start, end] of meetings.slice().sort((a, b) => a[0] - b[0])) {
    while (busy.size > 0 && busy.peek()[0] <= start) available.push(busy.pop()[1]);
    let room;
    let finish;
    if (available.size > 0) {
      room = available.pop();
      finish = end;
    } else {
      const entry = busy.pop();
      room = entry[1];
      finish = entry[0] + end - start;
    }
    counts[room] += 1;
    busy.push([finish, room]);
  }
  let answer = 0;
  for (let room = 1; room < n; room += 1) if (counts[room] > counts[answer]) answer = room;
  return answer;
}

const mostBooked = solve;
class Solution {
  mostBooked(n, meetings) { return solve(n, meetings); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostBooked };
