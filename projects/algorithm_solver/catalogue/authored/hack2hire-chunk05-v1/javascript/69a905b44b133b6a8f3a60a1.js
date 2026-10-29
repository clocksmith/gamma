// Original hack2hire:69a905b44b133b6a8f3a60a1; inferred public-preview contract; qualification unknown.
"use strict";
class CryptoOrderManager {
  constructor() { this.orders = new Map(); }
  apply(message) {
    const parts = message.split(',').map(v => v.trim());
    if (parts.length !== 5) return false;
    const [id, side, symbol, raw, event] = parts;
    if (!/^[0-9]+$/.test(raw) || !['NEW','FILLED'].includes(event)) return false;
    const quantity = BigInt(raw), row = this.orders.get(id);
    if (quantity <= 0n) return false;
    if (event === 'NEW') {
      if (row) return row.operation === side && row.symbol === symbol && row.total === quantity;
      this.orders.set(id, {id, operation: side, symbol, total: quantity, filled: 0n, remaining: quantity}); return true;
    }
    if (!row || row.operation !== side || row.symbol !== symbol || quantity > row.remaining) return false;
    row.filled += quantity; row.remaining -= quantity; return true;
  }
  status(orderId) { const row = this.orders.get(orderId); return row ? {...row} : null; }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "CryptoOrderManager") throw new Error("exact constructor trace required");
  const instance = new CryptoOrderManager(...argumentLists[0]), result = [null], allowed = new Set(["apply", "status"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.CryptoOrderManager = CryptoOrderManager;
