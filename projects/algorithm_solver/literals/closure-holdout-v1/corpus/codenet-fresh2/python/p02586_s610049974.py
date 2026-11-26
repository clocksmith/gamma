import sys
input = sys.stdin.readline

R, C, K = map(int, input().split())

items = [0] * R * C

for _ in range(K):
    r, c, v = map(int, input().split())
    items[C * (r-1) + c-1] = v

dp = [0] * 4 * R * C

dp[1] = items[0]

def ind(i,j,k):
    return 4 * C * i + 4 * j + k

for row in range(R):
    for col in range(C):
        for pick in range(4):
            curr = dp[ind(row,col,pick)]
            #Go Right
            if col + 1 < C:
                dp[ind(row,col+1,pick)] = max(curr, dp[ind(row,col+1,pick)])
                if pick < 3:
                    dp[ind(row,col+1,pick+1)] = max(curr + items[C * row + col+1], dp[ind(row,col+1,pick+1)])
            #Go Down
            if row + 1 < R:
                dp[ind(row+1,col,0)] = max(curr, dp[ind(row+1,col,0)])
                dp[ind(row+1,col,1)] = max(curr + items[C * (row+1) + col], dp[ind(row+1,col,1)])
                    

print(max(dp))
            
