"""379. Design Phone Directory."""
class PhoneDirectory:
    def __init__(self, maxNumbers: int):
        self.available = list(range(maxNumbers - 1, -1, -1))
        self.used = set()

    def get(self) -> int:
        if not self.available:
            return -1
        number = self.available.pop()
        self.used.add(number)
        return number

    def check(self, number: int) -> bool:
        return number not in self.used

    def release(self, number: int) -> None:
        if number in self.used:
            self.used.remove(number)
            self.available.append(number)

def solve(maxNumbers: int, operations: list[str], arguments: list[list[int]]) -> list:
    directory = PhoneDirectory(maxNumbers)
    return [getattr(directory, operation)(*values) for operation, values in zip(operations, arguments)]
