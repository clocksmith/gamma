"""722. Remove Comments. Carry a partial output line across block comments, discarding only empty resulting lines."""

def solve(source: list[str]) -> list[str]:
    answer, buffer = [], []
    inside = False
    for line in source:
        i = 0
        while i < len(line):
            pair = line[i:i + 2]
            if inside:
                if pair == '*/':
                    inside = False
                    i += 2
                else:
                    i += 1
            elif pair == '//':
                break
            elif pair == '/*':
                inside = True
                i += 2
            else:
                buffer.append(line[i])
                i += 1
        if not inside and buffer:
            answer.append(''.join(buffer))
            buffer = []
    return answer


class Solution:
    def removeComments(self, source: list[str]) -> list[str]:
        return solve(source)
