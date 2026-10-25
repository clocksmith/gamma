class Solution:
    def videoStitching(self, clips: list[list[int]], time: int) -> int:
        if time == 0:
            return 0
        ordered = sorted(clips, key=lambda clip: clip[0])
        index = 0
        covered = 0
        count = 0
        while covered < time:
            furthest = covered
            while index < len(ordered) and ordered[index][0] <= covered:
                furthest = max(furthest, ordered[index][1])
                index += 1
            if furthest == covered:
                return -1
            covered = furthest
            count += 1
        return count
