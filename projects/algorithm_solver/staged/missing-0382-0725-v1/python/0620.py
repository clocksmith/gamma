"""620. Not Boring Movies. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. cinema: id, movie, description, rating. Output: all four columns, ordered by descending rating."""

def solve(cinema):
    return [{'id': row['id'], 'movie': row['movie'], 'description': row['description'], 'rating': row['rating']}
            for row in sorted(cinema, key=lambda item: -item['rating'])
            if row['id'] % 2 == 1 and row['description'] is not None and row['description'] != 'boring']


class Solution:
    def notBoringMovies(self, cinema):
        return solve(cinema)
