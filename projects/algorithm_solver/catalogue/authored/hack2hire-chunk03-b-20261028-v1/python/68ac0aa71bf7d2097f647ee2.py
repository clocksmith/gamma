"""Hack2Hire 68ac0aa71bf7d2097f647ee2 (Most Frequent Call Chain) over an INFERRED spec; qualification unknown."""


def solve(traces):
    child = {}
    parent, name, count = [-1], [''], [0]  # node 0 is the empty chain; node ids follow first-record order
    stack = [0]
    for trace in traces:
        if trace[:2] == '->':
            key = (stack[-1], trace[3:])
            node = child.get(key)
            if node is None:
                node = len(parent)
                child[key] = node
                parent.append(stack[-1]); name.append(trace[3:]); count.append(0)
            count[node] += 1
            stack.append(node)
        else:
            stack.pop()
    best = 0
    for node in range(1, len(count)):
        if count[node] > count[best]: best = node
    chain = []
    while best > 0:
        chain.append(name[best])
        best = parent[best]
    return chain[::-1]


class Solution:
    def mostFrequentCallChain(self, traces):
        return solve(traces)
