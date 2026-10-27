"""595. Big Countries. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. world: name, continent, area, population, gdp. Output: name, population, area."""

def solve(world):
    return [{'name': row['name'], 'population': row['population'], 'area': row['area']}
            for row in world if (row['area'] is not None and row['area'] >= 3_000_000)
            or (row['population'] is not None and row['population'] >= 25_000_000)]


class Solution:
    def bigCountries(self, world):
        return solve(world)
