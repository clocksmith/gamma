"""Original ExamRoom development candidate; qualification unknown."""
from bisect import insort

class ExamRoom:
    def __init__(self, n):
        self.n = n
        self.occupied = []

    def seat(self):
        seat, distance = 0, self.occupied[0] if self.occupied else self.n
        for a,b in zip(self.occupied,self.occupied[1:]):
            candidate = (b-a)//2
            if candidate > distance:
                seat,distance = a+candidate,candidate
        if self.occupied and self.n-1-self.occupied[-1] > distance:
            seat = self.n-1
        insort(self.occupied,seat)
        return seat

    def leave(self, p):
        self.occupied.remove(p)
