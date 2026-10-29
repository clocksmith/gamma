"""Original frontend 774 variant; qualification unknown."""


def solve(stations, k: int) -> float:
    gaps = [stations[i + 1] - stations[i] for i in range(len(stations) - 1)]
    lo, hi = 0.0, float(stations[-1] - stations[0])
    for _ in range(60):
        mid = (lo + hi) * 0.5
        need = sum(int((g - 1e-12) // mid) for g in gaps)
        if need <= k:
            hi = mid
        else:
            lo = mid
    return round(hi, 6)


minmaxGasDist = solve


class Solution:
    def minmaxGasDist(self, stations, k: int) -> float:
        return solve(stations, k)
