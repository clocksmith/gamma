"""Original candidate; no qualification or admission."""

import heapq

class MovieRentingSystem:
    def __init__(self,n,entries):
        self.records={};self.available={};self.rented=[]
        for shop,movie,price in entries:self.records[shop,movie]=[price,0,False];self.available.setdefault(movie,[]).append((price,shop,0))
        for heap in self.available.values():heapq.heapify(heap)
    def search(self,movie):
        heap=self.available.get(movie,[]);kept=[]
        while heap and len(kept)<5:
            entry=heapq.heappop(heap);price,shop,version=entry;record=self.records[shop,movie]
            if not record[2] and record[1]==version:kept.append(entry)
        for entry in kept:heapq.heappush(heap,entry)
        return [shop for _,shop,_ in kept]
    def rent(self,shop,movie):
        record=self.records[shop,movie];record[1]+=1;record[2]=True;heapq.heappush(self.rented,(record[0],shop,movie,record[1]))
    def drop(self,shop,movie):
        record=self.records[shop,movie];record[1]+=1;record[2]=False;heapq.heappush(self.available[movie],(record[0],shop,record[1]))
    def report(self):
        kept=[]
        while self.rented and len(kept)<5:
            entry=heapq.heappop(self.rented);_,shop,movie,version=entry;record=self.records[shop,movie]
            if record[2] and record[1]==version:kept.append(entry)
        for entry in kept:heapq.heappush(self.rented,entry)
        return [[shop,movie] for _,shop,movie,_ in kept]


def solve(operations, arguments):
    instance = MovieRentingSystem(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
