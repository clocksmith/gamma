"""2383. Minimum Hours of Training to Win a Competition (Easy).

Specification: https://leetcode.com/problems/minimum-hours-of-training-to-win-a-competition/description/
"""


def solve(
    initialEnergy: int,
    initialExperience: int,
    energy: list[int],
    experience: list[int],
) -> int:
    """O(n) time, O(1) auxiliary space; preserve both opponent arrays."""
    total_energy = sum(energy)
    hours = max(0, total_energy + 1 - initialEnergy)
    current_experience = initialExperience
    for required in experience:
        if current_experience <= required:
            extra = required + 1 - current_experience
            hours += extra
            current_experience += extra
        current_experience += required
    return hours


class Solution:
    def minNumberOfHours(
        self,
        initialEnergy: int,
        initialExperience: int,
        energy: list[int],
        experience: list[int],
    ) -> int:
        return solve(initialEnergy, initialExperience, energy, experience)
