"""618. Students Report By Geography. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. student: name, continent in America/Asia/Europe. Output columns: America, Asia, Europe, with names independently alphabetized and NULL padding."""

def solve(student):
    groups = {continent: [] for continent in ('America', 'Asia', 'Europe')}
    for row in student:
        groups[row['continent']].append(row['name'])
    for names in groups.values():
        names.sort()
    height = max((len(names) for names in groups.values()), default=0)
    return [{continent: names[i] if i < len(names) else None for continent, names in groups.items()}
            for i in range(height)]


class Solution:
    def geographyReport(self, student):
        return solve(student)
