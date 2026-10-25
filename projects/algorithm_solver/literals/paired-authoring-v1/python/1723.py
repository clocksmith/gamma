def can_assign(jobs: list[int], workers: int, limit: int) -> bool:
    loads = [0] * workers

    def place(index: int) -> bool:
        if index == len(jobs):
            return True
        seen = set()
        for worker in range(workers):
            previous = loads[worker]
            if previous in seen:
                continue
            seen.add(previous)
            if previous + jobs[index] <= limit:
                loads[worker] += jobs[index]
                possible = place(index + 1)
                loads[worker] -= jobs[index]
                if possible:
                    return True
            if previous == 0:
                break
        return False

    return place(0)


class Solution:
    def minimumTimeRequired(self, jobs: list[int], k: int) -> int:
        ordered = sorted(jobs, reverse=True)
        left = ordered[0]
        right = sum(ordered)
        while left < right:
            middle = left + (right - left) // 2
            if can_assign(ordered, k, middle):
                right = middle
            else:
                left = middle + 1
        return left
