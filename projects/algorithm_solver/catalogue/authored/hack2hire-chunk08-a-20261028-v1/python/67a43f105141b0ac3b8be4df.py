"""Hack2Hire 67a43f105141b0ac3b8be4df (Recipes From Ingredients) over an INFERRED spec; qualification unknown."""


def solve(recipes, ingredients):
    supply = [0] * 26
    for ch in ingredients:
        supply[ord(ch) - 97] += 1
    count = 0
    for recipe in recipes:
        need = [0] * 26
        ok = True
        for ch in recipe:
            c = ord(ch) - 97
            need[c] += 1
            if need[c] > supply[c]:
                ok = False
                break
        if ok:
            count += 1
    return count


class Solution:
    def countRecipes(self, recipes, ingredients):
        return solve(recipes, ingredients)
