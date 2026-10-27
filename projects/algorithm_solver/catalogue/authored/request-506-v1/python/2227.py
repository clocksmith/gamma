"""Original candidate for LeetCode 2227. Contract: https://leetcode.com/problems/encrypt-and-decrypt-strings/
Development tests only; not admitted or independently qualified.
Batch adapter solve(operations, arguments) follows Encrypter class-call arrays.
Complexity: O(total dictionary characters + query characters) expected time; O(dictionary encoding size) space"""
from collections import Counter

def solve(operations,arguments):
    keys,values,dictionary=arguments[0];mapping=dict(zip(keys,values))
    def encrypt(word):
        if any(c not in mapping for c in word):return ''
        return ''.join(mapping[c] for c in word)
    counts=Counter(encrypt(word) for word in dictionary if all(c in mapping for c in word));out=[None]
    for op,a in zip(operations[1:],arguments[1:]):out.append(encrypt(a[0]) if op=='encrypt' else counts[a[0]])
    return out
