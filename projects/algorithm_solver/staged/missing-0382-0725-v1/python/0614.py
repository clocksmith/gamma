"""614. Second Degree Follower. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. follow: followee, follower; pairs are unique. Output: follower, num, ordered by follower."""

def solve(follow):
    following = {row['follower'] for row in follow}
    counts = {}
    for row in follow:
        counts[row['followee']] = counts.get(row['followee'], 0) + 1
    return [{'follower': user, 'num': counts[user]} for user in sorted(counts) if user in following]


class Solution:
    def secondDegreeFollower(self, follow):
        return solve(follow)
