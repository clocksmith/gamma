"""Original hack2hire:69a905614b133b6a8f3a609c; inferred public-preview contract; qualification unknown."""
class CryptoOrderManager:
    def __init__(self):
        self.orders = {}

    def apply(self, message):
        parts = [v.strip() for v in message.split(',')]
        if len(parts) != 5:
            return False
        oid, side, symbol, raw, event = parts
        if not raw.isascii() or not raw.isdecimal() or event not in ('NEW', 'FILLED'):
            return False
        quantity = int(raw)
        if quantity <= 0:
            return False
        row = self.orders.get(oid)
        if event == 'NEW':
            if row is not None:
                return (row['operation'], row['symbol'], row['total']) == (side, symbol, quantity)
            self.orders[oid] = {'id': oid, 'operation': side, 'symbol': symbol, 'total': quantity, 'filled': 0, 'remaining': quantity}
            return True
        if row is None or row['operation'] != side or row['symbol'] != symbol or quantity > row['remaining']:
            return False
        row['filled'] += quantity
        row['remaining'] -= quantity
        return True

    def status(self, orderId):
        row = self.orders.get(orderId)
        return dict(row) if row is not None else None

def solve(operation_names, argument_lists):
    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != 'CryptoOrderManager':
        raise ValueError("exact constructor trace required")
    instance = CryptoOrderManager(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('apply', 'status'):
            raise ValueError("unknown method")
        result.append(getattr(instance, name)(*arguments))
    return result
