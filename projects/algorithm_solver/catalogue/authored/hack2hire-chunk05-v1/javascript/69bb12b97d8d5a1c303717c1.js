// Original hack2hire:69bb12b97d8d5a1c303717c1; inferred public-preview contract; qualification unknown.
"use strict";
class TradingSystem {
  constructor() { this.items = new Map(); this.sequence = 0; }
  _less(a,b) { return a[0] < b[0] || a[0] === b[0] && a[1] < b[1]; }
  addListing(seller, item, price) {
    if (!this.items.has(item)) this.items.set(item, []);
    const heap = this.items.get(item), entry = [price, this.sequence++, seller]; heap.push(entry);
    let i = heap.length-1;
    while (i) { const p = Math.floor((i-1)/2); if (!this._less(heap[i],heap[p])) break; [heap[i],heap[p]] = [heap[p],heap[i]]; i = p; }
  }
  buy(item, budget) {
    const heap = this.items.get(item);
    if (!heap || !heap.length || heap[0][0] > budget) return null;
    const top = heap[0], last = heap.pop();
    if (heap.length) {
      heap[0] = last; let i = 0;
      while (true) {
        let best = i, left = i*2+1, right = left+1;
        if (left < heap.length && this._less(heap[left],heap[best])) best = left;
        if (right < heap.length && this._less(heap[right],heap[best])) best = right;
        if (best === i) break;
        [heap[i],heap[best]] = [heap[best],heap[i]]; i = best;
      }
    }
    return [top[2],top[0]];
  }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "TradingSystem") throw new Error("exact constructor trace required");
  const instance = new TradingSystem(...argumentLists[0]), result = [null], allowed = new Set(["addListing", "buy"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.TradingSystem = TradingSystem;
