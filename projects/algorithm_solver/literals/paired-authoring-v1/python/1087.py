class Solution:
    def expand(self, expression):
        results = [""]
        index = 0
        while index < len(expression):
            choices = []
            if expression[index] == "{":
                end = expression.index("}", index + 1)
                choices = expression[index + 1:end].split(",")
                index = end + 1
            else:
                choices.append(expression[index])
                index += 1
            expanded = []
            for prefix in results:
                for character in choices:
                    expanded.append(prefix + character)
            results = expanded
        return sorted(results)
