class Solution:
    def beforeAndAfterPuzzles(self, phrases):
        first_words = []
        last_words = []
        for phrase in phrases:
            words = phrase.split(" ")
            first_words.append(words[0])
            last_words.append(words[-1])
        answers = set()
        for left, phrase in enumerate(phrases):
            for right, suffix in enumerate(phrases):
                if left != right and last_words[left] == first_words[right]:
                    answers.add(phrase + suffix[len(first_words[right]):])
        return sorted(answers)
