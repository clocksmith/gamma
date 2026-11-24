n,T=map(int,input().split())
s=input()
s=s.replace("^","**")
time=eval(s)*T
if time>10**9:
    print("TLE")
else:
    print(time)
