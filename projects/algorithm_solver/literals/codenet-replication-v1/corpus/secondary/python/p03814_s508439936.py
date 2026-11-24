s = input()
n = len(s)
ma = n+1
mz = -1
for i in range(0 , n):
	if s[i]=='A':
		ma = min(ma, i)
	if s[i]=='Z':
		mz = max(mz, i)

if ma>mz:
	print(0)
else:
	print(mz-ma+1)