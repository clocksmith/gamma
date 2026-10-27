# Original candidate implementation. Contract: https://leetcode.com/problems/stock-price-fluctuation/
import heapq

class StockPrice:
    def __init__(self): self.prices={};self.latest=0;self.low=[];self.high=[]
    def update(self,timestamp,price):
        self.prices[timestamp]=price;self.latest=max(self.latest,timestamp)
        heapq.heappush(self.low,(price,timestamp));heapq.heappush(self.high,(-price,timestamp))
    def current(self):return self.prices[self.latest]
    def minimum(self):
        while self.prices[self.low[0][1]]!=self.low[0][0]:heapq.heappop(self.low)
        return self.low[0][0]
    def maximum(self):
        while self.prices[self.high[0][1]]!=-self.high[0][0]:heapq.heappop(self.high)
        return -self.high[0][0]

def solve(operations,arguments):
    obj=None;out=[]
    for op,args in zip(operations,arguments):
        if op=='StockPrice':obj=StockPrice();out.append(None)
        else:out.append(getattr(obj,op)(*args))
    return out
