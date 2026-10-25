def solve(words):
    owners = {}
    for index, word in enumerate(words):
        unique = set()
        for start in range(len(word)):
            for end in range(start + 1, len(word) + 1):
                unique.add(word[start:end])
        for substring in unique:
            if substring not in owners:
                owners[substring] = index
            elif owners[substring] != index:
                owners[substring] = -1
    result = []
    for index, word in enumerate(words):
        answer = ""
        for length in range(1, len(word) + 1):
            for start in range(len(word) - length + 1):
                substring = word[start:start + length]
                if owners[substring] == index and (not answer or substring < answer):
                    answer = substring
            if answer:
                break
        result.append(answer)
    return result
