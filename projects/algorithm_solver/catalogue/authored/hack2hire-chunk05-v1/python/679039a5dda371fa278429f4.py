"""Original hack2hire:679039a5dda371fa278429f4; inferred public-preview contract; qualification unknown."""
class CryptoTradingSystem:
    def __init__(self):
        self.orders = {}

    def place(self, id, currency, amount, timestamp, type):
        if id in self.orders:
            return False
        self.orders[id] = {'id': id, 'currency': currency, 'amount': amount, 'timestamp': timestamp, 'type': type, 'state': 'live'}
        return True

    def _transition(self, id, allowed, target):
        row = self.orders.get(id)
        if row is None or row['state'] not in allowed:
            return False
        row['state'] = target
        return True

    def pause(self, id):
        return self._transition(id, ('live',), 'paused')

    def resume(self, id):
        return self._transition(id, ('paused',), 'live')

    def cancel(self, id):
        return self._transition(id, ('live', 'paused'), 'canceled')

    def complete(self, id):
        return self._transition(id, ('live',), 'completed')

    def listLive(self, currency):
        return [dict(row) for row in sorted(self.orders.values(), key=lambda r: (r['timestamp'], r['id'])) if row['state'] == 'live' and (currency is None or row['currency'] == currency)]

def solve(operation_names, argument_lists):
    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != 'CryptoTradingSystem':
        raise ValueError("exact constructor trace required")
    instance = CryptoTradingSystem(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('place', 'pause', 'resume', 'cancel', 'complete', 'listLive'):
            raise ValueError("unknown method")
        result.append(getattr(instance, name)(*arguments))
    return result
