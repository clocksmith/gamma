"""Independent formulations verify existing expectations; never rewrite them."""
import itertools


def permutation(n,k):
    # Direct lexicographic enumeration, independent of both factorial decoders.
    values=next(itertools.islice(itertools.permutations(range(1,n+1)),k-1,k))
    return ''.join(map(str,values))


def number(s):
    # Literal state machine for the published integer/decimal/exponent grammar.
    transitions={0:{'sign':1,'digit':2,'dot':3},1:{'digit':2,'dot':3},2:{'digit':2,'dot':4,'exp':5},3:{'digit':4},4:{'digit':4,'exp':5},5:{'sign':6,'digit':7},6:{'digit':7},7:{'digit':7}}
    state=0
    for c in s:
        kind='digit' if '0'<=c<='9' else 'sign' if c in '+-' else 'dot' if c=='.' else 'exp' if c in 'eE' else 'other'
        state=transitions.get(state,{}).get(kind,-1)
        if state==-1:return False
    return state in {2,4,7}


def matrix_contains(matrix,target):
    return any(value==target for row in matrix for value in row)


def contains(nums,target):
    return target in nums


def scramble(first,second):
    # Bottom-up length-indexed interval DP; no memoized recursive search.
    n=len(first)
    possible=[None]+[[[first[i]==second[j] for j in range(n)] for i in range(n)]]
    for length in range(2,n+1):
        size=n-length+1;layer=[[False]*size for _ in range(size)]
        for i in range(size):
            for j in range(size):
                layer[i][j]=any((possible[cut][i][j] and possible[length-cut][i+cut][j+cut]) or (possible[cut][i][j+length-cut] and possible[length-cut][i+cut][j]) for cut in range(1,length))
        possible.append(layer)
    return possible[n][0][0]


ORACLES={60:permutation,65:number,74:matrix_contains,81:contains,87:scramble}
