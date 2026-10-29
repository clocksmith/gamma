"""Original candidate; no qualification or admission."""

class AuthenticationManager:
    def __init__(self,timeToLive):self.ttl=timeToLive;self.expiry={}
    def generate(self,tokenId,currentTime):self.expiry[tokenId]=currentTime+self.ttl
    def renew(self,tokenId,currentTime):
        if self.expiry.get(tokenId,0)>currentTime:self.expiry[tokenId]=currentTime+self.ttl
    def countUnexpiredTokens(self,currentTime):return sum(expiry>currentTime for expiry in self.expiry.values())


def solve(operations, arguments):
    instance = AuthenticationManager(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
