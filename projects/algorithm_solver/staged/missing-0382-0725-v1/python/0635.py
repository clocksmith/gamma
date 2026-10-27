"""635. Design Log Storage System."""

class LogSystem:
    def __init__(self):
        self.logs = []

    def put(self, id: int, timestamp: str) -> None:
        self.logs.append((id, timestamp))

    def retrieve(self, start: str, end: str, granularity: str) -> list[int]:
        length = {'Year': 4, 'Month': 7, 'Day': 10, 'Hour': 13, 'Minute': 16, 'Second': 19}[granularity]
        low, high = start[:length], end[:length]
        return [identifier for identifier, timestamp in self.logs if low <= timestamp[:length] <= high]


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = LogSystem(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = LogSystem
