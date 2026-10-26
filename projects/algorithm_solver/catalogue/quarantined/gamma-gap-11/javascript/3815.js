'use strict';

// 3815. Design Auction System.
// O(Q log Q) total time and O(Q) storage over Q operations; versioned lazy heaps preserve updates and removals.
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

class AuctionSystem {
  constructor() {
    this.current = new Map();
    this.heaps = new Map();
    this.version = 0;
  }

  addBid(userId, itemId, bidAmount) {
    this.version += 1;
    if (!this.current.has(itemId)) {
      this.current.set(itemId, new Map());
      this.heaps.set(itemId, new Heap((left, right) => left[0] > right[0] || (left[0] === right[0] && left[1] > right[1])));
    }
    this.current.get(itemId).set(userId, [bidAmount, this.version]);
    this.heaps.get(itemId).push([bidAmount, userId, this.version]);
  }

  updateBid(userId, itemId, newAmount) {
    this.addBid(userId, itemId, newAmount);
  }

  removeBid(userId, itemId) {
    this.current.get(itemId).delete(userId);
  }

  getHighestBidder(itemId) {
    const heap = this.heaps.get(itemId);
    if (!heap) return -1;
    const current = this.current.get(itemId);
    while (heap.size > 0) {
      const [amount, user, version] = heap.peek();
      const record = current.get(user);
      if (record && record[0] === amount && record[1] === version) return user;
      heap.pop();
    }
    return -1;
  }
}

function solve(operations, argumentsList) {
  // Replay the native interface with one request-local instance.
  if (operations.length === 0) return [];
  const instance = new AuctionSystem(...argumentsList[0]);
  const result = [null];
  for (let index = 1; index < operations.length; index += 1) {
    const value = instance[operations[index]](...argumentsList[index]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = AuctionSystem;
if (typeof module !== 'undefined') module.exports = { solve, Solution, AuctionSystem };
