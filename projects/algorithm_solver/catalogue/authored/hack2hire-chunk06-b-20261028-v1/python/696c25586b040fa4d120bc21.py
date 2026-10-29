"""Hack2Hire 696c25586b040fa4d120bc21 (Latency Bucket Counter) over an INFERRED spec; qualification unknown."""

def solve(latencies, bucketWidth, numOfBuckets):
    counts = [0] * numOfBuckets
    last = numOfBuckets - 1
    for latency in latencies:
        bucket = latency // bucketWidth
        counts[bucket if bucket < last else last] += 1
    return counts


class Solution:
    def countLatencyBuckets(self, latencies, bucketWidth, numOfBuckets):
        return solve(latencies, bucketWidth, numOfBuckets)
