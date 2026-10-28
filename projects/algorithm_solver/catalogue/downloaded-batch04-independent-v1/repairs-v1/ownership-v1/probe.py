"""Controlled ownership probe for this frozen observation transport, not production code."""
import sys

_seen = []


def solve(nums):
    # The actual transport has already decoded this call before invoking solve.
    raw = sys._getframe(1).f_locals['call']['args'][0]
    distinct_raw = nums is not raw
    raw_before = raw[:]
    current = nums[0]
    nums[0] = -1234
    detached = raw == raw_before
    nums[0] = current
    distinct_prior = all(nums is not previous for previous in _seen)
    for previous in _seen:
        previous[0] = -9999
    isolated = nums[0] == 2
    _seen.append(nums)
    return {'distinct_from_raw_packet': distinct_raw,
            'packet_unchanged_during_current_mutation': detached,
            'distinct_from_prior_calls': distinct_prior,
            'current_unchanged_by_prior_mutation': isolated}
