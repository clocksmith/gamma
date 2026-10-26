"""2115. Find All Possible Recipes from Given Supplies: propagate available ingredients through recipe dependency counts."""


def solve(recipes: list[str], ingredients: list[list[str]], supplies: list[str]) -> list[str]:
    """O(r + e + s) expected time and space for recipes, ingredient entries, and supplies; inputs are read-only."""
    dependents = {}
    remaining = [len(required) for required in ingredients]
    for index, required in enumerate(ingredients):
        for ingredient in required:
            dependents.setdefault(ingredient, []).append(index)
    available = set(supplies)
    queue = list(dict.fromkeys(supplies))
    completed = [False] * len(recipes)
    for index, count in enumerate(remaining):
        if count == 0:
            completed[index] = True
            if recipes[index] not in available:
                available.add(recipes[index])
                queue.append(recipes[index])
    head = 0
    while head < len(queue):
        ingredient = queue[head]
        head += 1
        for index in dependents.get(ingredient, []):
            remaining[index] -= 1
            if remaining[index] == 0:
                completed[index] = True
                if recipes[index] not in available:
                    available.add(recipes[index])
                    queue.append(recipes[index])
    return [recipe for index, recipe in enumerate(recipes) if completed[index]]


class Solution:
    def findAllRecipes(self, recipes: list[str], ingredients: list[list[str]], supplies: list[str]) -> list[str]:
        return solve(recipes, ingredients, supplies)
