# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(s):
    children = [{}]
    node = start = 0
    answer = []
    for index, letter in enumerate(s):
        if letter in children[node]:
            node = children[node][letter]
        else:
            children[node][letter] = len(children)
            children.append({})
            answer.append(s[start:index + 1])
            start = index + 1
            node = 0
    return answer
