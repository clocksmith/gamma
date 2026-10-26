"""1452. People Whose List of Favorite Companies Is Not a Subset of Another List: compare company sets without changing their original lists."""


def solve(favoriteCompanies: list[list[str]]) -> list[int]:
    """O(n * S) expected time and O(S) auxiliary space, where S is total company membership; inputs are read-only."""
    companies = [set(names) for names in favoriteCompanies]
    result = []
    for index, names in enumerate(companies):
        if not any(index != other and len(names) <= len(candidates) and names <= candidates
                   for other, candidates in enumerate(companies)):
            result.append(index)
    return result


class Solution:
    def peopleIndexes(self, favoriteCompanies: list[list[str]]) -> list[int]:
        return solve(favoriteCompanies)
