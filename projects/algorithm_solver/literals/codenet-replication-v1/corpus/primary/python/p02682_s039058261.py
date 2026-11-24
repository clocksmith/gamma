A,B,C,K = input().split()
if int(A) >= int(K):
  print(K)
elif int(A)+int(B) >= int(K):
  print(A)
else:
  print(int(A) + int(A) + int(B) - int(K))