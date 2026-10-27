"""359. Logger Rate Limiter."""
class Logger:
    def __init__(self):
        self.next_allowed = {}

    def shouldPrintMessage(self, timestamp: int, message: str) -> bool:
        if timestamp < self.next_allowed.get(message, 0):
            return False
        self.next_allowed[message] = timestamp + 10
        return True

def solve(calls: list[list]) -> list[bool]:
    logger = Logger()
    return [logger.shouldPrintMessage(*call) for call in calls]
