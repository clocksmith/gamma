class Solution:
    def sortVowels(self, s: str) -> str:
        vowel_set = set("AEIOUaeiou")
        vowels = sorted(character for character in s if character in vowel_set)
        output = list(s)
        next_vowel = 0
        for index, character in enumerate(output):
            if character in vowel_set:
                output[index] = vowels[next_vowel]
                next_vowel += 1
        return "".join(output)
