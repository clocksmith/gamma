d = int(input())
c_l = list(map(int,input().split()))
s_l = [list(map(int,input().split())) for i in range(d)]

t_l = [int(input()) for i in range(d)]

last_l = [-1 for i in range(26)]

ans = 0
for day in range(d):
  contest_num = t_l[day]
  contest_num -= 1

  contest_val = s_l[day][contest_num]

  ans += contest_val
  last_l[contest_num] = day

  for i in range(26):
    ans -= c_l[i] * (day - last_l[i])

  print(ans)