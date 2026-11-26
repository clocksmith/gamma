MOD = 998244353
s = input()
n = len(s)
R = s.count("0") * 2 + s.count("1")
B = 2*n - R
rb = [[R, B] for _ in range(2*n)]
if s[0] == "0":
	rb[0] = [2, 0]
elif s[0] == "1":
	rb[0] = [1, 1]
else:
	rb[0] = [0, 2]
for i in range(1, n):
	if s[i] == "0":
		rb[i] = [rb[i-1][0] + 2, rb[i-1][1] + 0]
	elif s[i] == "1":
		rb[i] = [rb[i-1][0] + 1, rb[i-1][1] + 1]
	else:
		rb[i] = [rb[i-1][0] + 0, rb[i-1][1] + 2]

dp = [[0 for _ in range(R+1)] for _ in range(2*n)]
if rb[0][0] >= 1:
	dp[0][1] = 1
if rb[0][1] >= 1:
	dp[0][0] = 1
for i in range(1, 2*n):
	for j in range(R+1):
		if j > 0 and rb[i][0] >= j:
			dp[i][j] += dp[i-1][j-1]
			dp[i][j] %= MOD
		if j != i+1 and rb[i][1] >= i+1 - j:
			dp[i][j] += dp[i-1][j]
			dp[i][j] %= MOD

print(dp[2*n-1][R])