"""Hack2Hire 695d85f19c1c1f40daea73a0 (Design Token Limiter) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class TokenLimiter:
    def __init__(self):
        self.users = {}  # userId -> [maxTokens, refillAmount, refillInterval, tokens, lastRefill]

    def setPolicy(self, userId, maxTokens, refillAmount, refillInterval, timestamp):
        self.users[userId] = [maxTokens, refillAmount, refillInterval, maxTokens, timestamp]

    def _refill(self, bucket, timestamp):
        due = (timestamp - bucket[4]) // bucket[2]
        if due > 0:
            bucket[3] = min(bucket[0], bucket[3] + due * bucket[1])
            bucket[4] += due * bucket[2]

    def consume(self, userId, tokens, timestamp):
        bucket = self.users.get(userId)
        if bucket is None:
            return False
        self._refill(bucket, timestamp)
        if bucket[3] >= tokens:
            bucket[3] -= tokens
            return True
        return False

    def getTokens(self, userId, timestamp):
        bucket = self.users.get(userId)
        if bucket is None:
            return -1
        self._refill(bucket, timestamp)
        return bucket[3]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'TokenLimiter' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = TokenLimiter(*argument_lists[0])
    allowed = {'setPolicy', 'consume', 'getTokens'}
    voids = {'setPolicy'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
