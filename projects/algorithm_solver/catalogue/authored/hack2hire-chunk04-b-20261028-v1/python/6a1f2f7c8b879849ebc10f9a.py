"""Hack2Hire 6a1f2f7c8b879849ebc10f9a (Circular Storage Allocator) over an INFERRED spec; qualification unknown."""


def solve(totalSlots, requests):
    used = [False] * totalSlots
    free_count = totalSlots
    result = []
    for kind, start, size in requests:
        start, size = int(start), int(size)
        if kind == 'store':
            found = -1
            if free_count >= size:
                run = 0
                for offset in range(totalSlots + size - 1):
                    if used[(start + offset) % totalSlots]:
                        run = 0
                        continue
                    run += 1
                    if run >= size:
                        found = (start + offset - size + 1) % totalSlots
                        break
            if found >= 0:
                for j in range(size):
                    used[(found + j) % totalSlots] = True
                free_count -= size
            result.append(found)
        else:
            freed = 0
            for j in range(size):
                q = (start + j) % totalSlots
                if used[q]:
                    used[q] = False
                    freed += 1
            free_count += freed
            result.append(freed)
    return result


class Solution:
    def processRequests(self, totalSlots, requests):
        return solve(totalSlots, requests)
