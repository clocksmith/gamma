class Solution:
    def generateParenthesis(self, n: int) -> list[str]:
        combinations = []
        path = []

        def collect(open_count: int, close_count: int) -> None:
            if close_count == n:
                combinations.append("".join(path))
                return
            if open_count < n:
                path.append("(")
                collect(open_count + 1, close_count)
                path.pop()
            if close_count < open_count:
                path.append(")")
                collect(open_count, close_count + 1)
                path.pop()

        collect(0, 0)
        return combinations
