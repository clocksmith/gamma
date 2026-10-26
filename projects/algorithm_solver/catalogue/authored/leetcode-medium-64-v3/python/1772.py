"""1772. Sort Features by Popularity: count each feature once per response and preserve original tie order."""


def solve(features: list[str], responses: list[str]) -> list[str]:
    """O(S + f log f) expected time and O(S + f) space for response text S and f features; inputs are read-only."""
    counts = {feature: 0 for feature in features}
    for response in responses:
        for word in set(response.split()):
            if word in counts:
                counts[word] += 1
    order = sorted(range(len(features)), key=lambda index: (-counts[features[index]], index))
    return [features[index] for index in order]


class Solution:
    def sortFeatures(self, features: list[str], responses: list[str]) -> list[str]:
        return solve(features, responses)
