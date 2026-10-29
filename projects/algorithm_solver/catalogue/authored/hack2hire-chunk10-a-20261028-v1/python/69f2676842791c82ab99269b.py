"""Hack2Hire 69f2676842791c82ab99269b (Design Recipe Management System, variant 4 of 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class RecipeManager:
    def __init__(self):
        self.recipes = {}  # recipe id -> record
        self.by_name = {}  # lower-cased name -> recipe id
        self.count = 0
        self.by_ingredient = {}  # lower-cased ingredient -> set of recipe numbers

    def addRecipe(self, name, ingredients, steps):
        low = name.lower()
        if low in self.by_name:
            return ''
        self.count += 1
        recipe_id = 'recipe%d' % self.count
        rec = {'n': self.count, 'name': name, 'ingredients': list(ingredients), 'steps': list(steps), 'sum': 0, 'votes': 0}
        self.recipes[recipe_id] = rec
        self.by_name[low] = recipe_id
        self._index(rec, 1)
        return recipe_id

    def getRecipe(self, recipeId):
        rec = self.recipes.get(recipeId)
        return [] if rec is None else [rec['name'], list(rec['ingredients']), list(rec['steps'])]

    def updateRecipe(self, recipeId, name, ingredients, steps):
        rec = self.recipes.get(recipeId)
        if rec is None:
            return False
        low = name.lower()
        owner = self.by_name.get(low)
        if owner is not None and owner != recipeId:
            return False
        self._index(rec, -1)
        del self.by_name[rec['name'].lower()]
        self.by_name[low] = recipeId
        rec['name'], rec['ingredients'], rec['steps'] = name, list(ingredients), list(steps)
        self._index(rec, 1)
        return True

    def deleteRecipe(self, recipeId):
        rec = self.recipes.pop(recipeId, None)
        if rec is None:
            return False
        del self.by_name[rec['name'].lower()]
        self._index(rec, -1)
        return True

    def _index(self, rec, sign):
        for low in {g.lower() for g in rec['ingredients']}:
            if sign > 0:
                self.by_ingredient.setdefault(low, set()).add(rec['n'])
            else:
                self.by_ingredient[low].discard(rec['n'])

    def searchByIngredient(self, ingredient):
        return ['recipe%d' % n for n in sorted(self.by_ingredient.get(ingredient.lower(), ()))]

    def rateRecipe(self, recipeId, rating):
        rec = self.recipes.get(recipeId)
        if rec is None:
            return False
        rec['sum'] += rating
        rec['votes'] += 1
        return True

    def getTopRated(self, k):
        def better(a, b):  # exact: higher average (cross-multiplied), then lower id number
            left, right = a['sum'] * b['votes'], b['sum'] * a['votes']
            return left > right or (left == right and a['n'] < b['n'])
        rated = [rec for rec in self.recipes.values() if rec['votes']]
        if k < 64 and k < len(rated):
            best = []  # small selection buffer, best first
            for rec in rated:
                if len(best) == k and not better(rec, best[-1]):
                    continue
                i = len(best)
                while i > 0 and better(rec, best[i - 1]):
                    i -= 1
                best.insert(i, rec)
                if len(best) > k:
                    best.pop()
        else:
            from functools import cmp_to_key
            best = sorted(rated, key=cmp_to_key(lambda a, b: -1 if better(a, b) else 1 if better(b, a) else 0))[:k]
        return ['recipe%d' % rec['n'] for rec in best]

    def listByNamePrefix(self, prefix):
        p = prefix.lower()
        return [recipe_id for low, recipe_id in sorted(self.by_name.items()) if low.startswith(p)]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'RecipeManager' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = RecipeManager(*argument_lists[0])
    allowed = {'addRecipe', 'getRecipe', 'updateRecipe', 'deleteRecipe', 'searchByIngredient', 'rateRecipe', 'getTopRated', 'listByNamePrefix'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
