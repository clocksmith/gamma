"""Original candidate; no qualification or admission."""

import random

class _SkipNode:
    def __init__(self,value,level):self.value=value;self.next=[None]*level

class Skiplist:
    def __init__(self):self.head=_SkipNode(-1,16);self.level=1
    def search(self,target):
        node=self.head
        for level in range(self.level-1,-1,-1):
            while node.next[level] is not None and node.next[level].value<target:node=node.next[level]
        node=node.next[0];return node is not None and node.value==target
    def add(self,num):
        update=[self.head]*16;node=self.head
        for level in range(self.level-1,-1,-1):
            while node.next[level] is not None and node.next[level].value<num:node=node.next[level]
            update[level]=node
        height=1
        while height<16 and random.random()<.5:height+=1
        self.level=max(self.level,height);node=_SkipNode(num,height)
        for level in range(height):node.next[level]=update[level].next[level];update[level].next[level]=node
    def erase(self,num):
        update=[self.head]*16;node=self.head
        for level in range(self.level-1,-1,-1):
            while node.next[level] is not None and node.next[level].value<num:node=node.next[level]
            update[level]=node
        node=node.next[0]
        if node is None or node.value!=num:return False
        for level in range(self.level):
            if update[level].next[level] is node:update[level].next[level]=node.next[level]
        while self.level>1 and self.head.next[self.level-1] is None:self.level-=1
        return True


def solve(operations, arguments):
    instance = Skiplist(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
