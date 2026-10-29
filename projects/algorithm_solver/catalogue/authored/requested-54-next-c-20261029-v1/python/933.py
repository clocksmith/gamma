from collections import deque

class RecentCounter:
    def __init__(self):
        self.times = deque()

    def ping(self, t):
        self.times.append(t)
        while self.times[0] < t-3000:
            self.times.popleft()
        return len(self.times)
