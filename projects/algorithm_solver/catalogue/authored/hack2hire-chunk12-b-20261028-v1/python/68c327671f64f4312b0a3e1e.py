"""Hack2Hire 68c327671f64f4312b0a3e1e (Minimize Shopping Department Visits) over an INFERRED spec; qualification unknown."""


def solve(products, shoppingList):
    department = {name: dept for name, dept in products}
    return len({department[item] for item in shoppingList if item in department})


class Solution:
    def minDepartmentVisits(self, products, shoppingList):
        return solve(products, shoppingList)
