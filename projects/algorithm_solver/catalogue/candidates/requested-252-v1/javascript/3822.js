/**
 * 3822. Design Order Management System
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(operations, arguments).
 * Algorithm: Index active orders by ID and by (type, price); replay adapter only dispatches an explicit allowlist.
 * Complexity: Expected O(1) add/modify/cancel; O(r log r) sorted query for r matching IDs; O(number of active orders) state.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Mutates only the class instance. Returned ID arrays are copied snapshots; caller arguments are not mutated.
 * Interface: Native OrderManagementSystem class plus solve(operations, arguments) replay. JavaScript names its second formal argumentsList to avoid shadowing the special arguments object.
 * Specification: https://leetcode.com/problems/design-order-management-system/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3822.Design%20Order%20Management%20System/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: The statement permits any query order; candidates return ascending IDs for deterministic cross-language output. Invalid domain calls are not qualified.
 */

class OrderManagementSystem {
  constructor() {
    this.orders = new Map();
    this.buckets = new Map([["buy", new Map()], ["sell", new Map()]]);
  }
  addOrder(orderId, orderType, price) {
    this.orders.set(orderId, [orderType, price]);
    const prices = this.buckets.get(orderType);
    if (!prices.has(price)) prices.set(price, new Set());
    prices.get(price).add(orderId);
  }
  modifyOrder(orderId, newPrice) {
    const [orderType, oldPrice] = this.orders.get(orderId);
    if (oldPrice === newPrice) return;
    this.removeFromBucket(orderId, orderType, oldPrice);
    this.orders.set(orderId, [orderType, newPrice]);
    const prices = this.buckets.get(orderType);
    if (!prices.has(newPrice)) prices.set(newPrice, new Set());
    prices.get(newPrice).add(orderId);
  }
  cancelOrder(orderId) {
    const [orderType, price] = this.orders.get(orderId);
    this.orders.delete(orderId);
    this.removeFromBucket(orderId, orderType, price);
  }
  getOrdersAtPrice(orderType, price) {
    return [...(this.buckets.get(orderType).get(price) || [])].sort((a, b) => a - b);
  }
  removeFromBucket(orderId, orderType, price) {
    const prices = this.buckets.get(orderType);
    const bucket = prices.get(price);
    bucket.delete(orderId);
    if (bucket.size === 0) prices.delete(price);
  }
}

function solve(operations, argumentsList) {
  if (operations.length !== argumentsList.length || operations.length === 0 || operations[0] !== "OrderManagementSystem" || argumentsList[0].length !== 0) {
    throw new TypeError("Expected matching operations/arguments beginning with OrderManagementSystem().");
  }
  const instance = new OrderManagementSystem();
  const output = [null];
  const arities = new Map([["addOrder", 3], ["modifyOrder", 2], ["cancelOrder", 1], ["getOrdersAtPrice", 2]]);
  for (let index = 1; index < operations.length; index += 1) {
    const operation = operations[index];
    const parameters = argumentsList[index];
    if (!arities.has(operation) || parameters.length !== arities.get(operation)) throw new TypeError("Unsupported operation or argument count.");
    const value = instance[operation](...parameters);
    output.push(value === undefined ? null : value);
  }
  return output;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, OrderManagementSystem };
}
