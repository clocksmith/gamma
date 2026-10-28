from heapq import heapify, heappush, heappop


class EventManager:
    def __init__(self, events):
        self.active = dict(events)
        self.heap = [(-priority, event_id) for event_id, priority in events]
        heapify(self.heap)

    def updatePriority(self, eventId, newPriority):
        self.active[eventId] = newPriority
        heappush(self.heap, (-newPriority, eventId))

    def pollHighest(self):
        while self.heap:
            negative, event_id = heappop(self.heap)
            if self.active.get(event_id) == -negative:
                del self.active[event_id]
                return event_id
        return -1
