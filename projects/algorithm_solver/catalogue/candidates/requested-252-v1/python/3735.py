"""3735. Lexicographically Smallest String After Reverse II
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(s).
Algorithm: Exact suffix array, Kasai LCP, and range-minimum queries compare every prefix/suffix reversal as at most two source fragments.
Complexity: O(n log n) time; O(n) space. No quadratic string construction and no probabilistic hash equality.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Canonical solve(s). Native judge method name was not supplied or independently verified.
Specification: https://leetcode.com/problems/lexicographically-smallest-string-after-reverse-ii/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3735.Lexicographically%20Smallest%20String%20After%20Reverse%20II/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: The original string is reachable by the required length-one reversal. The final answer is constructed once; separators are outside the input alphabet.
"""

def solve(s):
    length = len(s)
    text = s + "{" + s[::-1] + "$"
    size = len(text)
    counts = [0] * 128
    for character in text:
        counts[ord(character)] += 1
    for index in range(1, len(counts)):
        counts[index] += counts[index - 1]
    suffixes = [0] * size
    for index in range(size - 1, -1, -1):
        code = ord(text[index])
        counts[code] -= 1
        suffixes[counts[code]] = index
    ranks = [0] * size
    classes = 1
    for index in range(1, size):
        if text[suffixes[index]] != text[suffixes[index - 1]]:
            classes += 1
        ranks[suffixes[index]] = classes - 1
    width = 1
    while width < size and classes < size:
        shifted = [(index - width) % size for index in suffixes]
        counts = [0] * classes
        for index in shifted:
            counts[ranks[index]] += 1
        for index in range(1, classes):
            counts[index] += counts[index - 1]
        ordered = [0] * size
        for index in reversed(shifted):
            rank = ranks[index]
            counts[rank] -= 1
            ordered[counts[rank]] = index
        new_ranks = [0] * size
        new_classes = 1
        for offset in range(1, size):
            current, previous = ordered[offset], ordered[offset - 1]
            if ranks[current] != ranks[previous] or ranks[(current + width) % size] != ranks[(previous + width) % size]:
                new_classes += 1
            new_ranks[current] = new_classes - 1
        suffixes, ranks, classes = ordered, new_ranks, new_classes
        width *= 2

    common = [0] * size
    shared = 0
    for index in range(size):
        rank = ranks[index]
        if rank == 0:
            shared = 0
            continue
        previous = suffixes[rank - 1]
        while index + shared < size and previous + shared < size and text[index + shared] == text[previous + shared]:
            shared += 1
        common[rank] = shared
        if shared:
            shared -= 1
    base = 1
    while base < size:
        base *= 2
    minimums = [size] * (2 * base)
    minimums[base:base + size] = common
    for index in range(base - 1, 0, -1):
        minimums[index] = min(minimums[2 * index], minimums[2 * index + 1])

    def longest_common(first, second):
        if first == second:
            return size - first
        left, right = sorted((ranks[first], ranks[second]))
        left, right = left + 1 + base, right + 1 + base
        answer = size
        while left < right:
            if left % 2:
                answer = min(answer, minimums[left])
                left += 1
            if right % 2:
                right -= 1
                answer = min(answer, minimums[right])
            left //= 2
            right //= 2
        return answer

    def is_smaller(candidate, incumbent):
        first_part = second_part = 0
        first_offset = second_offset = 0
        while first_part < len(candidate) and second_part < len(incumbent):
            first_start, first_length = candidate[first_part]
            second_start, second_length = incumbent[second_part]
            available = min(first_length - first_offset, second_length - second_offset)
            same = min(available, longest_common(first_start + first_offset, second_start + second_offset))
            if same < available:
                return text[first_start + first_offset + same] < text[second_start + second_offset + same]
            first_offset += same
            second_offset += same
            if first_offset == first_length:
                first_part += 1
                first_offset = 0
            if second_offset == second_length:
                second_part += 1
                second_offset = 0
        return False

    reverse_start = length + 1
    best = [(0, length)]
    for count in range(1, length + 1):
        prefix = [(reverse_start + length - count, count)]
        if count < length:
            prefix.append((count, length - count))
        if is_smaller(prefix, best):
            best = prefix
        suffix = []
        if count < length:
            suffix.append((0, length - count))
        suffix.append((reverse_start, count))
        if is_smaller(suffix, best):
            best = suffix
    return "".join(text[start:start + count] for start, count in best)
