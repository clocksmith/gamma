def solve(s):
    words = s.split(' ')
    def count(word):
        return sum(c in 'aeiou' for c in word)
    target = count(words[0])
    for i in range(1, len(words)):
        if count(words[i]) == target:
            words[i] = words[i][::-1]
    return ' '.join(words)


class Solution:
    def reverseWords(self, s):
        return solve(s)
