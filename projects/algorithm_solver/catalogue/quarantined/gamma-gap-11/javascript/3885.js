'use strict';

// 3885. Design Event Manager.
// O((n+q) log(n+q)) total time and O(n+q) storage; versioned lazy heap prioritizes the smallest ID on equal priority.
class Heap {
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
    if (this.values.length === 0) return undefined;
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

class EventManager {
  constructor(events) {
    this.current = new Map();
    this.heap = new Heap((left, right) => left[0] > right[0] || (left[0] === right[0] && left[1] < right[1]));
    this.version = 0;
    for (const [event, priority] of events) this.updatePriority(event, priority);
  }

  updatePriority(eventId, newPriority) {
    this.version += 1;
    this.current.set(eventId, [newPriority, this.version]);
    this.heap.push([newPriority, eventId, this.version]);
  }

  pollHighest() {
    while (this.heap.size > 0) {
      const [priority, event, version] = this.heap.pop();
      const current = this.current.get(event);
      if (current && current[0] === priority && current[1] === version) {
        this.current.delete(event);
        return event;
      }
    }
    return -1;
  }
}

function solve(operations, argumentsList) {
  // Replay the native interface with one request-local instance.
  if (operations.length === 0) return [];
  const instance = new EventManager(...argumentsList[0]);
  const result = [null];
  for (let index = 1; index < operations.length; index += 1) {
    const value = instance[operations[index]](...argumentsList[index]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = EventManager;
if (typeof module !== 'undefined') module.exports = { solve, Solution, EventManager };
