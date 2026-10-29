"""Hack2Hire 69f266df42791c82ab992697 (Design Recipe Management System, variant 2 of 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


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
        rec = {'n': self.count, 'name': name, 'ingredients': list(ingredients), 'steps': list(steps)}
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


def solve(operation_names, argument_lists):
    if operation_names[0] != 'RecipeManager' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = RecipeManager(*argument_lists[0])
    allowed = {'addRecipe', 'getRecipe', 'updateRecipe', 'deleteRecipe', 'searchByIngredient'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
