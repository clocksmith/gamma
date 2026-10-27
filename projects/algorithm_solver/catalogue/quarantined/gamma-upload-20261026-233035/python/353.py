"""353. Design Snake Game."""
from collections import deque

class SnakeGame:
    def __init__(self, width: int, height: int, food: list[list[int]]):
        self.width = width
        self.height = height
        self.food = food
        self.food_index = 0
        self.body = deque([(0, 0)])
        self.occupied = {(0, 0)}
        self.directions = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}

    def move(self, direction: str) -> int:
        dr, dc = self.directions[direction]
        row, column = self.body[-1]
        head = (row + dr, column + dc)
        tail = self.body[0]
        if not (0 <= head[0] < self.height and 0 <= head[1] < self.width):
            return -1
        eating = self.food_index < len(self.food) and list(head) == self.food[self.food_index]
        if not eating:
            self.body.popleft()
            self.occupied.remove(tail)
        if head in self.occupied:
            return -1
        self.body.append(head)
        self.occupied.add(head)
        if eating:
            self.food_index += 1
        return len(self.body) - 1

def solve(width: int, height: int, food: list[list[int]], moves: list[str]) -> list[int]:
    game = SnakeGame(width, height, food)
    return [game.move(direction) for direction in moves]
