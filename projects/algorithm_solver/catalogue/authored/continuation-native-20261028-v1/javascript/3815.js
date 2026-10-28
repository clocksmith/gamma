"use strict";

class AuctionSystem {
  constructor() {
    this.bids = new Map();
    this.heaps = new Map();
  }
  _higher(left, right) {
    return left[0] > right[0] || (left[0] === right[0] && left[1] > right[1]);
  }
  _push(heap, value) {
    let at = heap.length;
    heap.push(value);
    while (at > 0) {
      const parent = Math.floor((at - 1) / 2);
      if (!this._higher(value, heap[parent])) break;
      heap[at] = heap[parent];
      at = parent;
    }
    heap[at] = value;
  }
  _pop(heap) {
    const last = heap.pop();
    if (heap.length === 0) return;
    let at = 0;
    while (2 * at + 1 < heap.length) {
      let child = 2 * at + 1;
      if (child + 1 < heap.length && this._higher(heap[child + 1], heap[child])) child++;
      if (!this._higher(heap[child], last)) break;
      heap[at] = heap[child];
      at = child;
    }
    heap[at] = last;
  }
  addBid(userId, itemId, bidAmount) {
    if (!this.bids.has(itemId)) this.bids.set(itemId, new Map());
    if (!this.heaps.has(itemId)) this.heaps.set(itemId, []);
    this.bids.get(itemId).set(userId, bidAmount);
    this._push(this.heaps.get(itemId), [bidAmount, userId]);
  }
  updateBid(userId, itemId, newAmount) {
    this.addBid(userId, itemId, newAmount);
  }
  removeBid(userId, itemId) {
    this.bids.get(itemId).delete(userId);
  }
  getHighestBidder(itemId) {
    const heap = this.heaps.get(itemId) || [];
    const live = this.bids.get(itemId);
    while (heap.length > 0) {
      const [amount, user] = heap[0];
      if (live && live.get(user) === amount) return user;
      this._pop(heap);
    }
    return -1;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "AuctionSystem" || argumentLists[0].length !== 0) throw new Error("exact constructor required");
  const instance = new AuctionSystem(), result = [null];
  const methods = new Set(["addBid", "updateBid", "removeBid", "getHighestBidder"]);
  for (let i = 1; i < operationNames.length; i++) {
    const name = operationNames[i];
    if (!methods.has(name)) throw new Error("unknown method");
    const value = instance[name](...argumentLists[i]);
    result.push(name === "getHighestBidder" ? value : null);
  }
  return result;
}

module.exports = solve;
module.exports.AuctionSystem = AuctionSystem;
