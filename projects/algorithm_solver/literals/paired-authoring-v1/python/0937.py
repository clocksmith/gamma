def letter_key(record):
    return record[0], record[1], record[2]


class Solution:
    def reorderLogFiles(self, logs: list[str]) -> list[str]:
        letters = []
        digits = []
        for index, log in enumerate(logs):
            separator = log.index(" ")
            identifier = log[:separator]
            content = log[separator + 1:]
            if "0" <= content[0] <= "9":
                digits.append(log)
            else:
                letters.append((content, identifier, index, log))
        letters.sort(key=letter_key)
        result = []
        for record in letters:
            result.append(record[3])
        for log in digits:
            result.append(log)
        return result
