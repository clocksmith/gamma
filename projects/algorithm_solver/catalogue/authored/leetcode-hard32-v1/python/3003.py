"""3003. Maximize the Number of Partitions After Operations."""

def solve(s: str, k: int) -> int:
    """O(26^2*n) time, O(n+26) space; evaluate each replacement through its next boundary."""
    if k == 26:
        return 1
    size = len(s)
    letters = [ord(char) - 97 for char in s]
    prefix_masks = [0] * size
    prefix_closed = [0] * size
    mask = closed = 0
    for index, letter in enumerate(letters):
        prefix_masks[index] = mask
        prefix_closed[index] = closed
        extended = mask | (1 << letter)
        if extended.bit_count() > k:
            closed += 1
            mask = 1 << letter
        else:
            mask = extended

    # next_start[i] is the end of the longest original valid prefix starting at i.
    next_start = [size] * size
    counts = [0] * 26
    right = distinct = 0
    for left in range(size):
        while right < size:
            letter = letters[right]
            if counts[letter] == 0 and distinct == k:
                break
            if counts[letter] == 0:
                distinct += 1
            counts[letter] += 1
            right += 1
        next_start[left] = right
        counts[letters[left]] -= 1
        if counts[letters[left]] == 0:
            distinct -= 1
    suffix_parts = [0] * (size + 1)
    for index in range(size - 1, -1, -1):
        suffix_parts[index] = 1 + suffix_parts[next_start[index]]

    answer = suffix_parts[0]
    next_position = [size] * 26
    for index in range(size - 1, -1, -1):
        order = sorted(range(26), key=next_position.__getitem__)
        mask = prefix_masks[index]
        count = mask.bit_count()
        for replacement in range(26):
            if replacement == letters[index]:
                continue
            bit = 1 << replacement
            completed = prefix_closed[index]
            if mask & bit:
                active = mask
                active_count = count
            elif count == k:
                completed += 1
                active = bit
                active_count = 1
            else:
                active = mask | bit
                active_count = count + 1
            needed = k - active_count + 1
            boundary = size
            for letter in order:
                if next_position[letter] == size:
                    break
                if active & (1 << letter) == 0:
                    needed -= 1
                    if needed == 0:
                        boundary = next_position[letter]
                        break
            # After this boundary, the untouched suffix starts a fresh greedy partition.
            answer = max(answer, completed + 1 + suffix_parts[boundary])
        next_position[letters[index]] = index
    return answer


class Solution:
    def maxPartitionsAfterOperations(self, s: str, k: int) -> int:
        return solve(s, k)
