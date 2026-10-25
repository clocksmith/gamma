class Solution:
    def removeVowels(self, text):
        kept = []
        for character in text:
            if character not in "aeiou":
                kept.append(character)
        return "".join(kept)
