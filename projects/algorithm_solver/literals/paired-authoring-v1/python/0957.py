class Solution:
    def prisonAfterNDays(self, cells, n):
        def next_day(state):
            following = [0] * 8
            for index in range(1, 7):
                following[index] = int(state[index - 1] == state[index + 1])
            return following

        state = cells[:]
        seen = {}
        day = 0
        while day < n:
            key = tuple(state)
            if key in seen:
                remaining = (n - day) % (day - seen[key])
                for _ in range(remaining):
                    state = next_day(state)
                return state
            seen[key] = day
            state = next_day(state)
            day += 1
        return state
