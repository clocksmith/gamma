"""3822. Design Order Management System
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(operations, arguments).
Algorithm: Index active orders by ID and by (type, price); replay adapter only dispatches an explicit allowlist.
Complexity: Expected O(1) add/modify/cancel; O(r log r) sorted query for r matching IDs; O(number of active orders) state.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Mutates only the class instance. Returned ID arrays are copied snapshots; caller arguments are not mutated.
Interface: Native OrderManagementSystem class plus solve(operations, arguments) replay. JavaScript names its second formal argumentsList to avoid shadowing the special arguments object.
Specification: https://leetcode.com/problems/design-order-management-system/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3822.Design%20Order%20Management%20System/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: The statement permits any query order; candidates return ascending IDs for deterministic cross-language output. Invalid domain calls are not qualified.
"""

class OrderManagementSystem:
    def __init__(self):
        self.orders = {}
        self.buckets = {"buy": {}, "sell": {}}

    def addOrder(self, orderId, orderType, price):
        self.orders[orderId] = (orderType, price)
        self.buckets[orderType].setdefault(price, set()).add(orderId)

    def modifyOrder(self, orderId, newPrice):
        order_type, old_price = self.orders[orderId]
        if old_price == newPrice:
            return
        self._remove_from_bucket(orderId, order_type, old_price)
        self.orders[orderId] = (order_type, newPrice)
        self.buckets[order_type].setdefault(newPrice, set()).add(orderId)

    def cancelOrder(self, orderId):
        order_type, price = self.orders.pop(orderId)
        self._remove_from_bucket(orderId, order_type, price)

    def getOrdersAtPrice(self, orderType, price):
        return sorted(self.buckets[orderType].get(price, ()))

    def _remove_from_bucket(self, order_id, order_type, price):
        bucket = self.buckets[order_type][price]
        bucket.remove(order_id)
        if not bucket:
            del self.buckets[order_type][price]


def solve(operations, arguments):
    if len(operations) != len(arguments) or not operations or operations[0] != "OrderManagementSystem" or arguments[0]:
        raise ValueError("Expected matching operations/arguments beginning with OrderManagementSystem().")
    instance = OrderManagementSystem()
    output = [None]
    allowed = {
        "addOrder": (instance.addOrder, 3),
        "modifyOrder": (instance.modifyOrder, 2),
        "cancelOrder": (instance.cancelOrder, 1),
        "getOrdersAtPrice": (instance.getOrdersAtPrice, 2),
    }
    for operation, parameters in zip(operations[1:], arguments[1:]):
        if operation not in allowed:
            raise ValueError("Unsupported operation.")
        method, arity = allowed[operation]
        if len(parameters) != arity:
            raise ValueError("Wrong argument count.")
        output.append(method(*parameters))
    return output
