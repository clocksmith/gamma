class Solution:
    def minimumBuckets(self, hamsters: str) -> int:
        cells = list(hamsters)
        buckets = 0
        for index in range(len(cells)):
            if cells[index] != "H":
                continue
            if index > 0 and cells[index - 1] == "B":
                continue
            if index + 1 < len(cells) and cells[index + 1] == ".":
                cells[index + 1] = "B"
            elif index > 0 and cells[index - 1] == ".":
                cells[index - 1] = "B"
            else:
                return -1
            buckets += 1
        return buckets
