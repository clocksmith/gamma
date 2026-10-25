class Solution:
    def highFive(self, items):
        leaders = {}
        for student, score in items:
            if student not in leaders:
                leaders[student] = []
            best = leaders[student]
            best.append(score)
            best.sort(reverse=True)
            if len(best) > 5:
                best.pop()
        result = []
        for student in sorted(leaders):
            result.append([student, sum(leaders[student]) // 5])
        return result
