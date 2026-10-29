"""Original hack2hire:68c6b9866211711bd990ccd5; inferred public-preview contract; qualification unknown."""
from copy import deepcopy

def retry(function, maxAttempts, initialDelay=0, multiplier=1, onDelay=None):
    if maxAttempts < 1:
        raise ValueError('maxAttempts must be positive')
    delay = initialDelay
    for attempt in range(maxAttempts):
        try:
            return function()
        except Exception:
            if attempt + 1 == maxAttempts:
                raise
        if onDelay is not None:
            onDelay(delay)
        delay *= multiplier

def retryOperation(outcomes, maxAttempts, initialDelay, multiplier):
    count = 0
    delays = []
    def operation():
        nonlocal count
        entry = outcomes[count] if count < len(outcomes) else {'error': 'exhausted'}
        count += 1
        if 'ok' in entry:
            return deepcopy(entry['ok'])
        raise RuntimeError(entry['error'])
    try:
        value = retry(operation, maxAttempts, initialDelay, multiplier, delays.append)
        return {'value': value, 'error': None, 'attempts': count, 'delays': delays}
    except RuntimeError as error:
        return {'value': None, 'error': str(error), 'attempts': count, 'delays': delays}

solve = retryOperation

class Solution:
    retryOperation = staticmethod(retryOperation)
