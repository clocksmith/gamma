"""608. Tree Node. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. tree: id, p_id (nullable). Output: id, type. Root classification takes precedence over leaf classification."""

def solve(tree):
    parents = {row['p_id'] for row in tree if row['p_id'] is not None}
    return [{'id': row['id'], 'type': 'Root' if row['p_id'] is None else 'Inner' if row['id'] in parents else 'Leaf'}
            for row in sorted(tree, key=lambda item: item['id'])]


class Solution:
    def treeNode(self, tree):
        return solve(tree)
