class Solution:
    def spellchecker(self, wordlist, queries):
        def vowel_key(lowered):
            return "".join("*" if char in "aeiou" else char for char in lowered)

        exact = set(wordlist)
        case_matches = {}
        vowel_matches = {}
        for word in wordlist:
            lowered = word.lower()
            masked = vowel_key(lowered)
            if lowered not in case_matches:
                case_matches[lowered] = word
            if masked not in vowel_matches:
                vowel_matches[masked] = word
        answer = []
        for query in queries:
            if query in exact:
                answer.append(query)
                continue
            lowered = query.lower()
            if lowered in case_matches:
                answer.append(case_matches[lowered])
            else:
                answer.append(vowel_matches.get(vowel_key(lowered), ""))
        return answer
