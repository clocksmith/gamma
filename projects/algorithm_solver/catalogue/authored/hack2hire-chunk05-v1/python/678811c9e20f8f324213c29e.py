"""Original hack2hire:678811c9e20f8f324213c29e; inferred public-preview contract; qualification unknown."""
from bisect import bisect_left

class MeetingScheduler:
    def __init__(self, rooms):
        self.rooms = list(rooms)
        self.bookings = {room: [] for room in rooms}

    def book(self, start, end):
        for room in self.rooms:
            rows = self.bookings[room]
            index = bisect_left(rows, (start,))
            if index and rows[index - 1][1] > start:
                continue
            if index < len(rows) and rows[index][0] < end:
                continue
            rows.insert(index, (start, end))
            return room
        return None

    def schedule(self, room):
        return [list(row) for row in self.bookings[room]]

def solve(operation_names, argument_lists):
    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != 'MeetingScheduler':
        raise ValueError("exact constructor trace required")
    instance = MeetingScheduler(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('book', 'schedule'):
            raise ValueError("unknown method")
        result.append(getattr(instance, name)(*arguments))
    return result
